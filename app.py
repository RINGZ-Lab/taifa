import os
import logging
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from listeners import register_listeners
from listeners.actions.task_socre_cal import calculate_absolute_difference, calculate_score, save_csv
from listeners.events.app_user_distribution import distribute_users
from ai.prompts.prompts import Prompts
from ai.providers import get_provider_response
from state_store.get_user_state import get_user_state, set_user_prompt, get_channel_task, set_channel_task
from listeners.events.ranking_system import post_ranking_interface, rankings, handle_move_up, handle_move_down
import re
import json
from typing import Dict, List

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

submission_state: Dict[str, Dict] = {}
task_submissions: Dict[str, Dict[int, bool]] = {}

@app.command("/select_prompt")
def handle_select_prompt(ack, body, client):
    ack()
    user_id = body["user_id"]
    channel_id = body["channel_id"]
    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text="Please select a prompt:",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Choose a prompt type:"},
                "accessory": {
                    "type": "static_select",
                    "action_id": "select_prompt",
                    "placeholder": {"type": "plain_text", "text": "Select a prompt"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Prompt 0"}, "value": "0"},
                        # {"text": {"type": "plain_text", "text": "Prompt 2"}, "value": "2"},
                        # {"text": {"type": "plain_text", "text": "Prompt 3"}, "value": "3"},

                    ]
                }
            }
        ]
    )
    logger.info(f"Prompt selection initiated for user {user_id} in channel {channel_id}")

@app.action("select_prompt")
def handle_prompt_selection(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    selected_value = body["actions"][0]["selected_option"]["value"]
    set_user_prompt(user_id, int(selected_value))
    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=f"Prompt {selected_value} has been selected."
    )
    logger.info(f"User {user_id} selected Prompt {selected_value} in channel {channel_id}")

@app.command("/distribute_users")
def handle_distribute_users(ack, body, client, logger):
    """
    Handles the /distribute_users slash command
    """
    try:
        ack()
        
        success = distribute_users(client)
        
        if success:
            client.chat_postEphemeral(
                channel=body["channel_id"],
                user=body["user_id"],
                text="Users have been successfully distributed into channels and anonymized."
            )
        else:
            client.chat_postEphemeral(
                channel=body["channel_id"],
                user=body["user_id"],
                text="There was an error distributing users. Please check the logs."
            )
            
    except Exception as e:
        logger.error(f"Error in distribute_users command: {e}")

@app.command("/rank_items")
def start_ranking(ack, body, client):
    ack()
    user_id = body["user_id"]
    channel_id = body["channel_id"]
    trigger_id = body["trigger_id"]
    post_ranking_interface(client, trigger_id, user_id, channel_id)

@app.action(re.compile("move_up_\d+"))
def move_up(ack, body, client):
    handle_move_up(ack, body, client)

@app.action(re.compile("move_down_\d+"))
def move_down(ack, body, client):
    handle_move_down(ack, body, client)


@app.view("submit_ranking")
def handle_ranking_submission(ack, body, client):
    ack()
    try:
        user_id = body["user"]["id"]
        view = body["view"]
        channel_id = view["private_metadata"]
        task_number = get_channel_task(channel_id)
        
        # Check if user has already submitted this task
        if user_id in task_submissions and task_number in task_submissions[user_id]:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="You have already submitted a ranking for this task."
            )
            return
            
        if user_id not in task_submissions:
            task_submissions[user_id] = {}
        task_submissions[user_id][task_number] = True
        
        if user_id in rankings and 'message_ts' in rankings[user_id]:
            try:
                client.chat_delete(
                    channel=channel_id,
                    ts=rankings[user_id]['message_ts']
                )
            except:
                pass
        
        task_number = get_channel_task(channel_id)
        
        if user_id not in rankings or task_number not in rankings[user_id]:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="No ranking found. Please start over."
            )
            return
            
        final_ranking = rankings[user_id][task_number]
        
        current_task = get_channel_task(channel_id)
        with open(f'./task/task{current_task}/expert_solution.json', 'r') as file:
            expert_solution = json.load(file)
            expert_ranking = expert_solution['expert_ranking']
        
        absolute_diff = calculate_absolute_difference(final_ranking, expert_ranking)
        score = calculate_score(absolute_diff)
        
        channel_info = client.conversations_info(channel=channel_id)
        channel_name = channel_info['channel']['name']
        
        members_response = client.conversations_members(channel=channel_id)
        members = [m for m in members_response['members'] 
                  if m != client.auth_test()["user_id"] and m != "USLACKBOT"]
        
        save_csv(channel_name, members, current_task, absolute_diff, score)
        
        ranking_text = (
            f"*<@{user_id}> Final Ranking submitted:*\n" + 
            "\n".join([f"{i+1}. {item}" for i, item in enumerate(final_ranking)]) +
            f"\n\n*Team Score: {score}%*"
        )
        
        submission_state[channel_id] = {
            'ranking': final_ranking,
            'user_id': user_id,
            'score': score,
            'expert_ranking': expert_ranking
        }
        
        _, selected_model = get_user_state(user_id, is_app_home=False)
        
        client.chat_postMessage(
            channel=channel_id,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ranking_text
                    }
                }
            ],
            text=f"Ranking submitted by <@{user_id}>"
        )
        
        evaluation_response = get_provider_response(
            client,
            user_id,
            selected_model,
            channel_id,
            Prompts.RANKING_EVALUATION_PROMPT.format(
                ranking=ranking_text,
                team_task=Prompts.TEAM_TASK_DESCRIPTION,
                score=score,
                expert_ranking="\n".join([f"{i+1}. {item}" for i, item in enumerate(expert_ranking)])
            ),
            context=[ranking_text]
        )
        
        client.chat_postMessage(
            channel=channel_id,
            text=f"*Team Performance Evaluation:*\n{evaluation_response}"
        )
        
        del rankings[user_id][task_number]
        if not rankings[user_id]:  # If user has no more tasks, clean up
            del rankings[user_id]
        
    except Exception as e:
        logger.error(f"Error handling ranking submission: {e}")

@app.action("start_ranking")
def handle_start_ranking(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    trigger_id = body["trigger_id"]
    post_ranking_interface(client, trigger_id, user_id, channel_id)

@app.action("select_task")
def handle_task_selection(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    selected_value = int(body["actions"][0]["selected_option"]["value"])

    try:
        set_channel_task(channel_id, selected_value)

        with open(f'./task/task{selected_value}/task.json', 'r') as file:
            task_data = json.load(file)

        scenario = task_data["sections"][0]["content"][0]["description"]
        items = task_data["sections"][1]["content"]
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"You have selected Task {selected_value} for this channel."
        )

        from listeners.events.canvas import create_canvas
        canvas_id = create_canvas(client, "Team Task", channel_id)
        
        if canvas_id:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="A canvas has been created for your team discussion. Please use the timer command when you're ready to start the task."
            )
        else:
            logger.error("Failed to create canvas after task selection")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Failed to create canvas. Please try again or contact support."
            )

    except Exception as e:
        logger.error(f"Error handling task selection: {e}")
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"Error selecting task: {str(e)}"
        )

@app.command("/select_task")
def handle_select_task(ack, body, client):
    ack()
    user_id = body["user_id"]
    channel_id = body["channel_id"]
    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text="Please select a task:",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Choose a task scenario:"},
                "accessory": {
                    "type": "static_select",
                    "action_id": "select_task",
                    "placeholder": {"type": "plain_text", "text": "Select a task"},
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "Task 1: Winter Survival"},
                            "value": "1"
                        },
                        {
                            "text": {"type": "plain_text", "text": "Task 2: Ocean Survival"},
                            "value": "2"
                        },
                        {
                            "text": {"type": "plain_text", "text": "Task 3: Moon Survival"},
                            "value": "3"
                        }
                    ]
                }
            }
        ]
    )
    logger.info(f"Task selection initiated for user {user_id} in channel {channel_id}")

register_listeners(app)
if __name__ == "__main__":
    logger.info("Starting the Slack app...")
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
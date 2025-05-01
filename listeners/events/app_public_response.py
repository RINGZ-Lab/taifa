from slack_sdk import WebClient
import logging
from slack_sdk.errors import SlackApiError
import json

from TeamEvaluationComponents.sentiment_analysis import get_team_sentiment
from ai.prompts.prompts import Prompts
from ai.providers import get_provider_response
from state_store.get_user_state import get_user_state, get_user_prompt, get_channel_task
from ..listener_utils.listener_constants import state


logger = logging.getLogger(__name__)

def app_public_response(client: WebClient, channel_id: str, event: dict):
    if state["is_silent"]:
        return
    try:
        user_id = event.get("user")
        task_number = get_channel_task(channel_id)
        
        try:
            with open(f'./task/task{task_number}/task.json', 'r') as file:
                task_data = json.load(file)
                task_description = task_data["sections"][0]["content"][0]["description"]
        except Exception as e:
            logger.error(f"Error loading task description: {e}")
            task_description = ""

        logger.debug(f"User ID: {user_id}")
        provider_name, selected_model = get_user_state(user_id, is_app_home=False)
        conversation = client.conversations_history(channel=channel_id, include_all_metadata=True, inclusive=True, limit=999)["messages"]
        logger.debug(f"Conversation: {conversation}")
        user_id_to_name = {}
        members_response = client.conversations_members(channel=channel_id, limit=999)

        members = members_response["members"]
        client.chat_postMessage(channel=channel_id, text="@channel :  Generating feedback for the team, please wait...", link_names=True)
        for member_id in members:
            if member_id == client.auth_test()["user_id"] or member_id == "B07HYHHLAFR" or member_id == "USLACKBOT" or member_id == "U07J7LFC8LQ":
                continue
            user_info = client.users_info(user=member_id)
            if user_info.get("ok"):
                user_id_to_name[member_id] = user_info['user']['real_name']
            logger.debug(f"User info for member {member_id}: {user_info}")
        formatted_context = []
        for msg in conversation:
            if msg.get('user') not in [client.auth_test()["user_id"], "B07HYHHLAFR", "USLACKBOT", 'U07J7LFC8LQ'] and \
               "Task_started" not in msg.get('text', '') and \
               "Task_ended" not in msg.get('text', '') and \
               float(next((m['ts'] for m in conversation if "Task_started" in m.get('text', '')), 0)) <= float(msg.get('ts', 0)) <= float(next((m['ts'] for m in conversation if "Task_ended" in m.get('text', '')), float('inf'))):
                formatted_context.append(f"{user_id_to_name.get(msg.get('user'), 'Unknown User')}: {msg.get('text', '')}")
                if msg.get('reply_count', 0) > 0:
                    thread_ts = msg['ts']
                    try:
                        thread_messages = client.conversations_replies(channel=channel_id, ts=thread_ts)["messages"]
                        for thread_msg in thread_messages[1:]:  # Skip the parent message
                            if thread_msg.get('user') not in [client.auth_test()["user_id"], "B07HYHHLAFR", "USLACKBOT"]:
                                formatted_context.append(f"{user_id_to_name.get(thread_msg.get('user'), 'Unknown User')}: {thread_msg.get('text', '')}")
                    except SlackApiError as e:
                        logger.error(f"Error fetching thread messages: {e.response['error']}")

        logger.debug(f"Formatted context: {formatted_context}")

        selected_prompt_number = get_user_prompt(user_id)
        if not selected_prompt_number:
            logger.error(f"No prompt selected for user {user_id}")
            return
# add prompt selection logic here and update the prompts in prompts.py
        team_prompt = {
            0: Prompts.TEAM_FEEDBACK,
            # 1: Prompts.TEAM_FEEDBACK_PROMPT_1,
            # 2: Prompts.TEAM_FEEDBACK_PROMPT_2,
            # 3: Prompts.TEAM_FEEDBACK_PROMPT_3,
        }.get(selected_prompt_number, None)

        logger.debug(f"Using team prompt: {team_prompt}")
        conversation_texts = [entry.split(": ", 1)[1] for entry in formatted_context]
        logger.debug(f"Conversation texts: {conversation_texts}")
        team_sentiment = get_team_sentiment(conversation_texts)
        sentiment_score = team_sentiment['compound']
        sentiment_label = (
            "positive" if sentiment_score > 0.05
            else "negative" if sentiment_score < -0.05
            else "neutral"
        )

        format_params = {
            'sentiment': f"{sentiment_label} ({sentiment_score:.2f})" if '{sentiment}' in team_prompt else '',
            'team_size': len(user_id_to_name) if '{team_size}' in team_prompt else '',
            'conversation_length': len(formatted_context) if '{conversation_length}' in team_prompt else '',
            'team_task': task_description
        }
        logger.debug(f"Format params: {format_params}")
        logger.debug(f"Selected prompt number: {selected_prompt_number}")
        logger.debug(f"context: {formatted_context}")
        logger.debug(f"Sentiment score: {sentiment_score}")
        logger.debug(f"Sentiment label: {sentiment_label}")
        logger.debug(f"Team size: {len(user_id_to_name)}")
        logger.debug(f"Conversation length: {len(formatted_context)}")
        logger.debug(f"Team task: {format_params['team_task']}")


        formatted_team_prompt = team_prompt.format(**format_params)
        logger.debug(f"Formatted team prompt: {formatted_team_prompt}")



        response = get_provider_response(
            client, 
            user_id, 
            selected_model,  
            channel_id,
            formatted_team_prompt,
            formatted_context
        )
        logger.debug(f"Generated response: {response}")
        client.chat_postMessage(channel=channel_id, text=f"@channel : \n {response}", link_names=True)
        logger.debug(f"Public message sent to channel {channel_id}")
        client.chat_postMessage(channel=channel_id, text=f"Team feedback generated")
        logger.debug(f"Public indicator message sent to channel {channel_id}")

    except SlackApiError as e:
        error_message = f"Slack API error occurred: {e.response['error']}"
        logger.error(error_message)
        client.chat_postMessage(channel=channel_id, text=error_message)

    except Exception as e:
        error_message = f"Error occurred: {e}"
        logger.error(f"Error sending public message to channel {channel_id}: {e}")
        client.chat_postMessage(channel=channel_id, text=error_message)

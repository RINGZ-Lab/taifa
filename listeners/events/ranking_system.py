from typing import Dict, List
from slack_sdk import WebClient
import logging
import json
import random
from state_store.get_user_state import get_channel_task

logger = logging.getLogger(__name__)

rankings: Dict[str, Dict[int, List[str]]] = {}
submission_state: Dict[str, Dict] = {}
task_submissions: Dict[str, Dict[int, bool]] = {}

def load_survival_items(channel_id: str):
    try:
        task_number = get_channel_task(channel_id)
        file_path = f'./task/task{task_number}/task.json'
        
        with open(file_path, 'r') as file:
            canvas_data = json.load(file)
            return [item['item'] for item in canvas_data['sections'][1]['content']]
    except Exception as e:
        logger.error(f"Error loading items from canvas: {e}")
        return []

def post_ranking_after_timer(client: WebClient, channel_id: str):
    try:
        task_number = get_channel_task(channel_id)
        
        if channel_id in submission_state:
            del submission_state[channel_id]
            
        for user_id in list(task_submissions.keys()):
            if task_number in task_submissions[user_id]:
                del task_submissions[user_id][task_number]
            if not task_submissions[user_id]:
                del task_submissions[user_id]
                
        for user_id in list(rankings.keys()):
            if task_number in rankings[user_id]:
                del rankings[user_id][task_number]
            if not rankings[user_id]:
                del rankings[user_id]
        
        members_response = client.conversations_members(channel=channel_id)
        members = members_response['members']
        bot_id = client.auth_test()['user_id']
        # this remove the admin and the bot from the list of members that submit the ranking
        human_members = [m for m in members if m != bot_id and m != "USLACKBOT" and m != "U07J7LFC8LQ"]
        if not human_members:
            logger.error("No human members found in channel")
            return
        selected_member = random.choice(human_members)
        trigger_id = None

        client.chat_postMessage(
            channel=channel_id,
            text=f"<@{selected_member}> has been randomly selected to provide the team's ranking!"
        )
        
        post_ranking_interface(client, trigger_id, selected_member, channel_id)
        
    except Exception as e:
        logger.error(f"Error in post_ranking_after_timer: {e}")

def post_ranking_interface(client: WebClient, trigger_id: str, user_id: str, channel_id: str):
    task_number = get_channel_task(channel_id)
    
    if user_id not in rankings:
        rankings[user_id] = {}
    
    rankings[user_id][task_number] = load_survival_items(channel_id)
    
    view = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "Survival Kit Ranking"
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit Ranking"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "callback_id": "submit_ranking",
        "private_metadata": channel_id,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Prioritize Your Survival Items"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_Rank these items from most crucial (1) to least crucial (7)_"
                }
            },
            {
                "type": "divider"
            }
        ]
    }
    
    item_details = get_item_details(channel_id)
    for index, item in enumerate(rankings[user_id][task_number]):
        details = item_details[item]
        view["blocks"].extend([
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": f"https://via.placeholder.com/24/{details['color'].replace('#', '')}/FFFFFF?text={index + 1}",
                        "alt_text": f"Rank {index + 1}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*{item}*"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_{details['desc']}_"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Move Up"
                        },
                        "style": "primary",
                        "action_id": f"move_up_{index}",
                        "value": str(index)
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Move Down"
                        },
                        "style": "danger",
                        "action_id": f"move_down_{index}",
                        "value": str(index)
                    }
                ]
            },
            {
                "type": "divider"
            }
        ])

    try:
        if not trigger_id:
            message = client.chat_postEphemeral(
                user=user_id,
                channel=channel_id,
                text=f"<@{user_id}> Click the button below to start ranking",
                blocks=[{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<@{user_id}> Click the button below to start ranking",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Start Ranking"
                        },
                        "action_id": "start_ranking"
                    }
                }]
            )
            if message and 'message_ts' in message:
                rankings[user_id]['message_ts'] = message['ts']
        else:
            if user_id in task_submissions and task_number in task_submissions[user_id]:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="You have already submitted a ranking for this task."
                )
                return
            
            client.views_open(
                trigger_id=trigger_id,
                view=view
            )
    except Exception as e:
        logger.error(f"Error opening ranking view: {e}")

def create_updated_view(items: List[str], channel_id: str) -> dict:
    """Create an updated view with the current ranking"""
    view = {
        "type": "modal",
        "title": {
            "type": "plain_text", 
            "text": "Survival Kit Ranking"
        },
        "submit": {
            "type": "plain_text", 
            "text": "Submit Ranking"
        },
        "close": {
            "type": "plain_text",
            "text": "Close"
        },
        "callback_id": "submit_ranking",
        "private_metadata": channel_id,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Current Ranking Order"
                }
            },
            {
                "type": "divider"
            }
        ]
    }
    
    item_details = get_item_details(channel_id)
    
    for index, item in enumerate(items):
        details = item_details[item]
        view["blocks"].extend([
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": f"https://via.placeholder.com/24/{details['color'].replace('#', '')}/FFFFFF?text={index + 1}",
                        "alt_text": f"Rank {index + 1}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*{item}*"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"_{details['desc']}_"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Move Up"
                        },
                        "style": "primary",
                        "action_id": f"move_up_{index}",
                        "value": str(index)
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Move Down"
                        },
                        "style": "danger",
                        "action_id": f"move_down_{index}",
                        "value": str(index)
                    }
                ]
            },
            {
                "type": "divider"
            }
        ])
    
    return view

def get_item_details(channel_id: str):
    try:
        task_number = get_channel_task(channel_id)
        file_path = f'./task/task{task_number}/task.json'
        with open(file_path, 'r') as file:
            canvas_data = json.load(file)
            return {
                item['item']: {
                    "desc": item['description'],
                    "color": "#4A154B" 
                }
                for item in canvas_data['sections'][1]['content']
            }
    except Exception as e:
        logger.error(f"Error loading item details: {e}")
        return {}

def handle_move_up(ack, body, client):
    ack()
    try:
        user_id = body["user"]["id"]
        view = body["view"]
        channel_id = view["private_metadata"]
        task_number = get_channel_task(channel_id)
        index = int(body["actions"][0]["action_id"].split("_")[-1])

        if index > 0 and user_id in rankings and task_number in rankings[user_id]:
            items = rankings[user_id][task_number]
            items[index], items[index-1] = items[index-1], items[index]

            client.views_update(
                view_id=view["id"],
                hash=view["hash"],
                view=create_updated_view(items, channel_id)
            )

    except Exception as e:
        logger.error(f"Error handling move up: {e}")

def handle_move_down(ack, body, client):
    ack()
    try:
        user_id = body["user"]["id"]
        view = body["view"]
        channel_id = view["private_metadata"]
        task_number = get_channel_task(channel_id)
        index = int(body["actions"][0]["action_id"].split("_")[-1])

        if user_id in rankings and task_number in rankings[user_id]:
            items = rankings[user_id][task_number]
            if index < len(items) - 1:
                items[index], items[index+1] = items[index+1], items[index]

                client.views_update(
                    view_id=view["id"],
                    hash=view["hash"],
                    view=create_updated_view(items, channel_id)
                )

    except Exception as e:
        logger.error(f"Error handling move down: {e}")
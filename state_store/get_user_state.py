import json
import os
from typing import Dict
from slack_sdk import WebClient

from state_store.user_identity import UserIdentity
import logging

logger = logging.getLogger(__name__)

def get_user_state(user_id: str, is_app_home: bool):
    filepath = f"./data/{user_id}"
    if not is_app_home and not os.path.exists(filepath):
        return {
            'o1-preview'
        }
    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as file:
                user_identity: UserIdentity = json.load(file)
                return user_identity["provider"], user_identity["model"]
    except Exception as e:
        logger.error(e)
        raise e


def get_user_profile(client: WebClient, user_id: str):
    try:
        response = client.users_profile_get(user=user_id)
        if response["ok"]:
            profile = response["profile"]
            return {
                'real_name': profile.get("real_name", ""),
                'title': profile.get("title", ""),
                'display_name': profile.get("display_name", "")
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching user profile for {user_id}: {e}")
        return None


user_state = {}

def set_user_prompt(user_id, prompt_number):
    if user_id not in user_state:
        user_state[user_id] = {}
    user_state[user_id]['selected_prompt'] = prompt_number

def get_user_prompt(user_id):
    return user_state.get(user_id, {}).get('selected_prompt', None)


channel_tasks: Dict[str, int] = {}

def get_channel_task(channel_id: str) -> int:
    return channel_tasks.get(channel_id, 1)

def set_channel_task(channel_id: str, task_number: int) -> None:
    if not 1 <= task_number <= 3:
        raise ValueError("Task number must be between 1 and 3")

    channel_tasks[channel_id] = task_number
    logger.info(f"Set task {task_number} for channel {channel_id}")
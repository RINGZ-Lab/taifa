from typing import Optional, List, Dict
from slack_sdk.web.slack_response import SlackResponse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)
def get_user_name(client: WebClient, user_id: str) -> str:
    try:
        response = client.users_info(user=user_id)
        return response['user']['real_name']
    except SlackApiError as e:
        logger.error(f"Error fetching user info for {user_id}: {e.response['error']}")
        return user_id

def parse_conversation(client: WebClient, messages):
    parsed_data = []

    for message in messages:
        if 'bot_id' in message:
            user_id = message.get('bot_id', 'Unknown Bot')
            user_name = message.get('bot_profile', {}).get('name', 'Unknown Bot')
        else:
            user_id = message.get('user', 'Unknown User')
            try:
                user_info = client.users_info(user=user_id)
                user_name = user_info['user']['name'] if user_info['ok'] else 'Unknown User'
            except SlackApiError as e:
                logger.error(f"Error fetching user info for {user_id}: {e.response['error']}")
                user_name = 'Unknown User'

        # Extract timestamp
        timestamp = message.get('ts', 'Unknown Timestamp')
        text = message.get('text', '')

        if 'blocks' in message:
            for block in message['blocks']:
                if block['type'] == 'rich_text':
                    for element in block['elements']:
                        if element['type'] == 'rich_text_section':
                            for sub_element in element['elements']:
                                if sub_element['type'] == 'text':
                                    text += sub_element['text']
        parsed_data.append({
            'user_id': user_id,
            'user_name': user_name,
            'timestamp': timestamp,
            'text': text
        })

    return parsed_data
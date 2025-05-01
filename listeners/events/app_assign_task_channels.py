from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging

logger = logging.getLogger(__name__)

def assign_task_to_channels(client: WebClient, channels: list, task_message: str):
    for channel_id in channels:
        try:
            client.chat_postMessage(channel=channel_id, text=task_message)
        except SlackApiError as e:
            logger.error(f"Error sending task to channel {channel_id}: {e.response['error']}")
import random
import logging
import os
from slack_sdk import WebClient
from ..utils.channel_manager import distribute_users_to_channels

logger = logging.getLogger(__name__)

def distribute_users(client: WebClient):
    try:
        response = client.users_list()
        user_ids = [
            user["id"] for user in response["members"] 
            if not user["is_bot"] and user["id"] != "USLACKBOT"
        ]
        user_client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))
        channels = distribute_users_to_channels(client, user_ids, user_client)
        
        if channels:
            logger.info(f"Users have been distributed and anonymized in channels: {channels}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error in user distribution and anonymization: {e}")
        return False
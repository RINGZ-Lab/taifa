from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.anonymous_names import generate_anonymous_name
import random
import time
import logging
import os
"""
This function is used to create a channel in slack workspace
then invite users to the channel those users are distributed in groups of 3 to different channels randomly
"""
logger = logging.getLogger(__name__)

# add user id that you should not get a feedback.
previous_users = []

def handle_rate_limited(error_response):
    retry_after = int(error_response.headers.get('Retry-After', 1))
    logger.debug(f"Rate limited. Retrying after {retry_after} seconds...")
    time.sleep(retry_after)

def create_channel(client: WebClient, channel_name: str):
    channel_name = channel_name.lower().replace(" ", "-")[:21]
    try:
        response = client.conversations_create(name=channel_name, is_private=True)
        return response["channel"]["id"]
    except SlackApiError as e:
        if e.response['error'] == 'name_taken':
            unique_channel_name = f"{channel_name}-{int(time.time())}"
            try:
                response = client.conversations_create(name=unique_channel_name, is_private=True)
                return response["channel"]["id"]
            except SlackApiError as e:
                logger.error(f"Error creating channel with unique name: {e.response['error']}")
                return None
        elif e.response['error'] == 'ratelimited':
            handle_rate_limited(e.response)
        logger.error(f"Error creating channel: {e.response['error']}")
        return None

def set_anonymous_profile(client: WebClient, user_id: str):
    try:
        anonymous_name = generate_anonymous_name()
        user_client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))
        try:
            client.chat_postEphemeral(
                channel=user_id,
                user=user_id,
                text=f"Your anonymous display name is: {anonymous_name}",
                timeout=10
            )
            logger.info(f"Successfully sent anonymous name to user {user_id}")
            try:
                name_parts = anonymous_name.split(" ") if " " in anonymous_name else [anonymous_name, ""]
                
                response = user_client.users_profile_set(
                    user=user_id,
                    profile={
                        "display_name": anonymous_name,
                        "first_name": name_parts[0],
                        "last_name": name_parts[1] if len(name_parts) > 1 else "",
                        "real_name": anonymous_name,
                        "status_text": "",
                        "status_emoji": ""
                    },
                    timeout=5
                )
                if response["ok"]:
                    logger.info(f"Successfully updated profile for user {user_id}")
                    return True
                    
            except SlackApiError as e:
                if e.response['error'] == 'not_allowed_token_type':
                    logger.warning(f"User token cannot modify profiles - using display name only for {user_id}")
                else:
                    logger.error(f"Error updating profile with user token: {e.response['error']}")
                return True
                
        except SlackApiError as e:
            logger.error(f"Error sending ephemeral message: {e.response['error']}")
            return False
            
    except Exception as e:
        logger.error(f"Error in set_anonymous_profile: {str(e)}")
        return False

def distribute_users_to_channels(client: WebClient, user_ids: list, user_client: WebClient = None, admin_id: str = 'U07J7LFC8LQ'):
    if admin_id in user_ids:
        user_ids.remove(admin_id)
    for previous_user in previous_users:
        if previous_user in user_ids:
            user_ids.remove(previous_user)

    random.shuffle(user_ids)
    channels = []
    num_users = len(user_ids)
    num_channels = (num_users + 2) // 3

    logger.debug(f"Total users (excluding admin): {num_users}, Number of channels needed: {num_channels}")

    for i in range(num_channels):
        channel_name = f"group_channel_{i + 1}"
        channel_id = create_channel(client, channel_name)
        if channel_id:
            channels.append(channel_id)
            group_users = user_ids[i*3:(i+1)*3]

            logger.debug(f"Channel {channel_name} created with ID {channel_id}. Users assigned: {group_users}")

            for user_id in group_users:
                if user_client:
                    try:
                        anonymous_name = generate_anonymous_name()
                        response = user_client.users_profile_set(
                            user=user_id,
                            profile={
                                "display_name": anonymous_name,
                                "first_name": anonymous_name,
                                "last_name": "",
                                "status_text": "",
                                "status_emoji": ""
                            }
                        )
                        if response["ok"]:
                            logger.info(f"Successfully set profile for user {user_id} using user token")
                            continue
                    except SlackApiError as e:
                        logger.warning(f"Failed to set profile with user token: {e.response['error']}")
                
                success = set_anonymous_profile(client, user_id)
                if not success:
                    logger.warning(f"Could not set anonymous profile for user {user_id}")

            try:
                client.conversations_invite(channel=channel_id, users=','.join(group_users))
                client.chat_postMessage(
                    channel=channel_id,
                    text="Welcome! 🎭 This is an anonymous channel. Please maintain anonymity in all interactions."
                )
            except SlackApiError as e:
                logger.error(f"Error inviting users to channel {channel_id}: {e.response['error']}")
                for error in e.response.get('errors', []):
                    logger.error(f"User {error['user']} invite error: {error['error']}")

    if admin_id:
        for channel_id in channels:
            try:
                client.conversations_invite(channel=channel_id, users=admin_id)
                logger.info(f"Admin {admin_id} added to channel {channel_id}")
            except SlackApiError as e:
                logger.error(f"Error adding admin to channel {channel_id}: {e.response['error']}")

    return channels





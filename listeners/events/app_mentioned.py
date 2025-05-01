from ai.prompts.prompts import Prompts
from ai.providers import get_provider_response
from logging import Logger
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import Say
import listeners
from ..listener_utils.listener_constants import DEFAULT_LOADING_TEXT, MENTION_WITHOUT_TEXT
from ..listener_utils.parse_conversation import parse_conversation
from ..listener_utils.listener_constants import state
from state_store.get_user_state import get_user_state
"""
Handles the event when the app is mentioned in a Slack channel, retrieves the conversation context,
and generates an AI response if text is provided, otherwise sends a default response
"""
def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    if state["is_silent"]:
        return
    try:
        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts")
        user_id = event.get("user")
        text = event.get("text")
        user_state = get_user_state(user_id, is_app_home=False)
        selected_model = user_state[1]
        if thread_ts:
            conversation = client.conversations_replies(channel=channel_id, ts=thread_ts)["messages"]
        else:
            conversation = client.conversations_history(channel=channel_id)["messages"]
            thread_ts = event["ts"]
        conversation = [
            # Filter out messages from the bot itself, replace XXXX with the bot ID
            f"{msg['user']}: {msg['text']}" for msg in conversation if 'user' in msg and msg['user'] != 'XXXXXX'
        ]
        logger.debug(f"Conversation: {conversation}")
        if text:
            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            response = get_provider_response(
                client=client,
                user_id=user_id,
                model_name=selected_model,
                channel_id=channel_id,
                prompt_template=Prompts.GENERAL_QUESTION.format(text=text,conversation=conversation),
                context=text
            )
            client.chat_update(channel=channel_id, ts=waiting_message["ts"], text=response)
        else:
            client.chat_postMessage(channel=channel_id, text=MENTION_WITHOUT_TEXT)

    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
        client.chat_postMessage(channel=channel_id, text=f"Received an error from AiFeedbackAgent:\n{e.response['error']}")

    except Exception as e:
        logger.error(f"General error: {e}")
        client.chat_postMessage(channel=channel_id, text=f"Received an error from AiFeedbackAgent:\n{e}")

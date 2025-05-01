from ai.ai_constants import DM_SYSTEM_CONTENT
from ai.providers import get_provider_response
from logging import Logger
from slack_bolt import Say
from slack_sdk import WebClient

from state_store.get_user_state import get_user_state
from ..listener_utils.listener_constants import DEFAULT_LOADING_TEXT
from ..listener_utils.parse_conversation import parse_conversation

"""
Handles the event when a direct message is sent to the agent, direct message use by default gpt4o.
"""


def app_messaged_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    user_id = event.get("user")
    selected_model = 'slack'

    try:
        if event.get("channel_type") == "im":
            conversation_context = []

            if thread_ts:
                conversation = client.conversations_replies(channel=channel_id, ts=thread_ts)["messages"]
                conversation_context = parse_conversation(client, conversation)

            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            response = get_provider_response(client, user_id, selected_model, conversation_context, "")
            client.chat_update(channel=channel_id, ts=waiting_message["ts"], text=str(response))
    except Exception as e:
        logger.error(e)
        client.chat_update(channel=channel_id, ts=waiting_message["ts"], text=f"Received an error from AiFeedbackBot:\n{e}")

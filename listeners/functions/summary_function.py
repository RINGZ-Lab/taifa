from ai.providers import get_provider_response
from logging import Logger
from slack_bolt import Complete, Fail, Ack
from slack_sdk import WebClient
import logging
from state_store.get_user_state import get_user_state
from ..listener_utils.listener_constants import SUMMARIZE_CHANNEL_WORKFLOW
from ..listener_utils.parse_conversation import parse_conversation

logger = logging.getLogger(__name__)
def handle_summary_function_callback(
    ack: Ack, inputs: dict, fail: Fail, logger: Logger, client: WebClient, complete: Complete
):
    ack()
    try:
        user_context = inputs["user_context"]
        channel_id = inputs["channel_id"]
        history = client.conversations_history(channel=channel_id)["messages"]
        conversation = parse_conversation(client, history)
        provider_name, selected_model = get_user_state(user_context["id"], is_app_home=False)

        summary = get_provider_response(client, user_context["id"], selected_model, conversation, channel_id, is_team_feedback=False)

        complete({"user_context": user_context, "response": summary})
    except Exception as e:
        logger.exception(e)
        fail(e)

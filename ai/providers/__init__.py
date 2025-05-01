from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from listeners.listener_utils.parse_conversation import get_user_name
from .anthropic import AnthropicAPI
from .openai import Azure_API
from ..ai_constants import DEFAULT_SYSTEM_CONTENT
from state_store.get_user_state import get_user_state
from typing import Optional, List
from logging import Logger
import logging
from ..prompts.prompts import Prompts
"""
New AI providers must be added below.
`get_available_providers()`
This function retrieves available API models from different AI providers.
It combines the available models into a single dictionary.
`_get_provider()`
This function returns an instance of the appropriate API provider based on the given provider name.
`get_provider_response`()
This function retrieves the user's selected API provider and model,
sets the model, and generates a response.
Note that context is an optional parameter because some functionalities,
such as commands, do not allow access to conversation history if the bot
isn't in the channel where the command is run.
"""

logger = logging.getLogger(__name__)

def get_available_providers():
    return {**AnthropicAPI().get_models(), **Azure_API().get_models()}


def _get_provider(provider_name: str):
    if provider_name.lower() == "azure":
        return Azure_API()
    elif provider_name.lower() == "anthropic":
        return AnthropicAPI()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def get_provider_response(client: WebClient, user_id: str, model_name: str, channel_id: str,
                          prompt_template: str, context: Optional[List] = []) -> object:
    try:
        full_prompt = f"{prompt_template}\n\nContext:\n{context}\n\nBased on this, please provide the requested feedback."
        logger.debug(f"Full prompt for model {model_name}: {full_prompt}")

        provider = _get_provider("azure")
        provider.set_model(model_name)

        # Generate the response
        response = provider.generate_response(full_prompt, Prompts.SYSTEM_CONTENT)
        logger.debug(f"Response from provider for user {user_id}: {response}")

        return response
    except Exception as e:
        logger.error(f"Error in get_provider_response for user {user_id}: {e}")
        return f"An error occurred while generating the response: {str(e)}"
import os
import logging
from openai import AzureOpenAI
from .base_provider import BaseAPIProvider


logger = logging.getLogger(__name__)

class Azure_API(BaseAPIProvider):
    MODELS = {
        "slack": {
            "name": os.getenv("AZURE_MODEL_DEPLOYMENT_SLACK", "slack"),
            "provider": "Azure",
            "max_tokens": 16384
        },
        "o1-preview": {
            "name": os.getenv("AZURE_MODEL_DEPLOYMENT_O1_PREVIEW", "o1-preview"),
            "provider": "Azure",
            "max_completion_tokens": 32768
        },
        "o1-mini": {
            "name": os.getenv("AZURE_MODEL_DEPLOYMENT_O1_MINI", "o1-mini"),
            "provider": "Azure",
            "max_completion_tokens": 65536
        }
    }

    def __init__(self):
        self.api_key = os.getenv("AZURE_API_KEY")
        self.api_base = os.getenv("AZURE_ENDPOINT")
        self.api_version = "2024-08-01-preview"

        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.api_base,
            api_version=self.api_version
        )

        self.current_model = None
    def set_model(self, model_name: str):
        if model_name not in self.MODELS:
            raise ValueError(f"Invalid model: {model_name}")
        logger.debug(f"Attempting to set model to: {model_name}")

        self.current_model = model_name
        logger.debug(f"Model set to: {self.current_model}")

    def get_models(self) -> dict:
        if self.api_key:
            return self.MODELS
        else:
            logger.error("API key is missing.")
            return {}

    def generate_response(self, prompt: str, system_content: str) -> str:
        try:
            model_settings = self.MODELS[self.current_model]
            if not self.current_model:
                raise ValueError("No model is set. Please call set_model() before generating a response.")

            logger.debug(f"Using model: {model_settings['name']} for API call.")
            logger.debug(f"Calling API with prompt: {prompt}")

            messages = [{"role": "user", "content": prompt}]
            if self.current_model == "slack":
                messages.insert(0, {"role": "system", "content": system_content})

            if 'max_completion_tokens' in model_settings:
                api_params = {
                    "model": model_settings["name"],
                    "messages": messages,
                    "max_completion_tokens": model_settings["max_completion_tokens"],
                }
            else:
                api_params = {
                    "model": model_settings["name"],
                    "messages": messages,
                    "max_tokens": model_settings["max_tokens"],
                }

            if self.current_model == "slack":
                api_params.update({
                    "temperature": 0,
                    "top_p": 0.95,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                })

            response = self.client.chat.completions.create(**api_params)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"An error occurred while generating the response: {e}")
            raise e
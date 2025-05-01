import logging
import os
from slack_bolt import App, BoltResponse
from slack_bolt.oauth.callback_options import CallbackOptions, SuccessArgs, FailureArgs
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from listeners import register_listeners

logging.basicConfig(level=logging.DEBUG)
def success(args: SuccessArgs) -> BoltResponse:
    return args.default.success(args)

def failure(args: FailureArgs) -> BoltResponse:
    return args.default.failure(args)


app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    installation_store=FileInstallationStore(base_dir="./installations"),
    oauth_settings=OAuthSettings(
        client_id=os.environ.get("SLACK_CLIENT_ID"),
        client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
        scopes=["channels:history", "chat:write", "commands"],
        user_scopes=[],
        redirect_uri=None,
        install_path="/slack/install",
        redirect_uri_path="/slack/oauth_redirect",
        state_store=FileOAuthStateStore(expiration_seconds=600),
        callback_options=CallbackOptions(success=success, failure=failure),
    ),
)

register_listeners(app)

if __name__ == "__main__":
    app.start(3000)

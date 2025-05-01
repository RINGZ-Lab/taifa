from slack_bolt import App
from .app_home_opened import app_home_opened_callback
from .app_mentioned import app_mentioned_callback
from .app_messaged import app_messaged_callback
from .app_personal_message import app_personal_message



def register(app: App):
    app.event("app_home_opened")(app_home_opened_callback)
    app.event("app_mention")(app_mentioned_callback)
    app.event("message")(app_messaged_callback)
    app.event("app_personal")(app_personal_message)

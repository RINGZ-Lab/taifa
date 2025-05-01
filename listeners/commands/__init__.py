from slack_bolt import App
from .ask_command import ask_callback

from .timer import timer_callback


def register(app: App):
    app.command("/ask-AiFeedbackBot")(ask_callback)
    app.command("/timer")(timer_callback)


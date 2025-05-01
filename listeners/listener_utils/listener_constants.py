MENTION_WITHOUT_TEXT = """
Hi there! You didn't provide a message with your mention.
    Mention me again in this thread so that I can help you out!
"""
SUMMARIZE_CHANNEL_WORKFLOW = """
User has just joined this slack channel.
Create a quick summary of the conversation in this channel to cath up the user.
Don't use user names in your response.
"""
DEFAULT_LOADING_TEXT = "Thinking..."

state = {
    "is_silent": False
}
def set_timer():
    state["is_silent"] = True

def reset_timer():
    state["is_silent"] = False
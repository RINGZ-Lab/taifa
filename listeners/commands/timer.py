import time
import threading
from slack_bolt import Ack, Say, BoltContext
from slack_sdk import WebClient
from state_store.get_user_state import get_user_state, get_channel_task
from ..listener_utils.listener_constants import set_timer, reset_timer
from ..events.app_personal_message import app_personal_message
from ..events.app_public_response import app_public_response
from ..events.canvas import create_canvas
from ..events.ranking_system import post_ranking_after_timer
import logging
"""
Callback for handling the 'timer' command. It acknowledges the command, retrieves the user's ID and timer duration,
and keeps the bot silent for the specified duration.
"""
logger = logging.getLogger(__name__)
timer_threads = {}
stop_timers = {}
timer_locks = {}


def timer_callback(client: WebClient, ack: Ack, command, context: BoltContext):
    try:
        ack()
        logger.info("Timer command received.")
        user_id = context["user_id"]
        channel_id = context["channel_id"]
        input_text = command["text"].strip()

        if channel_id not in timer_threads:
            timer_threads[channel_id] = None
            stop_timers[channel_id] = threading.Event()
            timer_locks[channel_id] = threading.Lock()

        if input_text.lower() == "end":
            if timer_threads[channel_id] and timer_threads[channel_id].is_alive():
                stop_timers[channel_id].set()  # Signal the timer to stop
                client.chat_postEphemeral(channel=channel_id, user=user_id, text="Timer stopped.")
            else:
                client.chat_postEphemeral(channel=channel_id, user=user_id, text="No active timer to stop.")
            return

        if input_text.isdigit():
            duration = int(input_text)
            logger.info(f"Starting timer for {duration} seconds.")

            with timer_locks[channel_id]:
                if timer_threads[channel_id] and timer_threads[channel_id].is_alive():
                    client.chat_postEphemeral(
                        channel=channel_id, user=user_id, text="Timer is already running. Please wait or stop it first."
                    )
                    return

            stop_timers[channel_id].clear()
            _, selected_model = get_user_state(user_id, is_app_home=False)
            timer_threads[channel_id] = threading.Thread(target=start_timer, args=(duration, client, channel_id, user_id, selected_model))
            timer_threads[channel_id].start()

        else:
            client.chat_postEphemeral(
                channel=channel_id, user=user_id, text="Please provide a valid number of seconds or 'end' to stop the timer."
            )
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        client.chat_postEphemeral(channel=channel_id, user=user_id, text=f"An error occurred:\n{e}")

def start_timer(duration, client, channel_id, user_id):
    stop_timer = stop_timers[channel_id]
    timer_lock = timer_locks[channel_id]

    with timer_lock:
        set_timer()
        start_time = time.time()

        try:
            client.chat_postEphemeral(
                channel=channel_id, user=user_id, text=f"Task_started, Bot will be silent for {duration} seconds."
            )
            client.chat_postMessage(channel=channel_id, text="TO622 Task_started, Timer is running.")
        except Exception as e:
            logger.error(f"Error sending initial timer message: {e}")
            return

    sent_60_second_alert = False
    while time.time() - start_time < duration:
        if stop_timer.is_set():
            with timer_lock:
                try:
                    client.chat_postMessage(channel=channel_id, text="The timer has been stopped by the user.")
                    client.chat_postEphemeral(channel=channel_id, user=user_id, text="Timer has been stopped by the user.")
                except Exception as e:
                    logger.error(f"Error sending stop timer message: {e}")
            return

        if not sent_60_second_alert and duration - (time.time() - start_time) <= 60:
            try:
                client.chat_postMessage(channel=channel_id, text=f"@channel : ⏳ 60 seconds remaining. Please wrap up your discussions!", link_names=True)
                sent_60_second_alert = True
            except Exception as e:
                logger.error(f"Error sending 60 seconds remaining message: {e}")

        time.sleep(1)

    if not stop_timer.is_set():
        with timer_lock:
            reset_timer()
            text = "The bot is no longer silent. Here's a brief update on recent conversations."
            try:
                client.chat_postEphemeral(channel=channel_id, user=user_id, text="Task_ended, Timer is off.")
                client.chat_postMessage(channel=channel_id, text="Task time ended, Please stop writing and wait for the feedback.")
                client.chat_postMessage(
                    channel=channel_id,
                    text="A random team member will be selected to submit the team's ranking."
                )
                post_ranking_after_timer(client, channel_id)


                time.sleep(60)
                app_public_response(client=client, channel_id=channel_id, event={"user": user_id})
                app_personal_message(client=client, channel_id=channel_id, user_id=user_id, text=text)


            except Exception as e:
                logger.error(f"Error sending timer off message: {e}")

    stop_timer.clear()


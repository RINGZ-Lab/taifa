from TeamEvaluationComponents.words_spoken import words_spoken
from TeamEvaluationComponents.sentiment_analysis import get_team_sentiment
from TeamEvaluationComponents.lsm_module import LSM
from ai.providers import get_provider_response
import logging
from slack_sdk import WebClient
from state_store.get_user_state import get_user_state, get_user_profile, get_user_prompt, get_channel_task
from ..listener_utils.parse_conversation import get_user_name
from ..listener_utils.listener_constants import state
from ai.prompts.prompts import Prompts
import json
from slack_sdk.errors import SlackApiError


logger = logging.getLogger(__name__)


def app_personal_message(client: WebClient, channel_id: str, user_id: str, text: str):

    if state["is_silent"]:
        return
    try:
        task_number = get_channel_task(channel_id)
        if not task_number:
            logger.error(f"No task number found for channel {channel_id}")
            return
        try:
            with open(f'./task/task{task_number}/task.json', 'r') as file:
                task_data = json.load(file)
                task_description = task_data["sections"][0]["content"][0]["description"]
        except Exception as e:
            logger.error(f"Error loading task description: {e}")
            task_description = ""

        # user_name = get_user_name(client, user_id)
        provider_name, selected_model = get_user_state(user_id, is_app_home=False)
        selected_prompt_number = get_user_prompt(user_id)
        if not selected_prompt_number:
            logger.error(f"No prompt selected for user {user_id}")
            return
# you can add more prompts here, please update the prompt/prompt.py file
        individual_prompt = {
            0: Prompts.INDIVIDUAL_FEEDBACK,
            # 1: Prompts.INDIVIDUAL_FEEDBACK_PROMPT_1,
            # 2: Prompts.INDIVIDUAL_FEEDBACK_PROMPT_2,
        }.get(selected_prompt_number, None)

        if not channel_id:
            logger.error("Invalid channel ID provided.")
            return

        logger.debug(f"Channel ID: {channel_id}")
        conversation = client.conversations_history(channel=channel_id, include_all_metadata=True, inclusive=True, limit=999)["messages"]
        logger.debug(f"Conversation: {conversation}")

        # conversation_context = parse_conversation(client, conversation)
        conversation_context = []
        team_messages = []
        for msg in conversation:
            msg_user_id = msg.get('user', 'Unknown User')
            text = msg.get('text', '')
            timestamp = float(msg.get('ts', 0))
            task_start_ts = float(next((m['ts'] for m in conversation if "Task_started" in m.get('text', '')), 0))
            task_end_ts = float(next((m['ts'] for m in conversation if "Task_ended" in m.get('text', '')), float('inf')))
            
            if (msg_user_id in [client.auth_test()["user_id"], "B07HYHHLAFR", "USLACKBOT"] or
                "TO622" in text or
                "TO243" in text or
                timestamp < task_start_ts or
                timestamp > task_end_ts):
                continue
            
            user_name = get_user_name(client, msg_user_id)
            team_messages.append({f"{user_name}": text})
            user_profile = get_user_profile(client, msg_user_id)

            if user_profile:
                conversation_context.append({
                    "name": user_profile['real_name'],
                    "title": user_profile['title'],
                    "text": text,
                })
            if msg.get('reply_count', 0) > 0:
                thread_ts = msg['ts']
                try:
                    thread_messages = client.conversations_replies(channel=channel_id, ts=thread_ts)["messages"]
                    for thread_msg in thread_messages[1:]:
                        if thread_msg.get('user') not in [client.auth_test()["user_id"], "B07HYHHLAFR", "USLACKBOT"]:
                            user_name = get_user_name(client, thread_msg.get('user'))
                            conversation_context.append({
                                "name": user_name,
                                "title": user_profile['title'],
                                "text": thread_msg.get('text', '')
                            })
                except SlackApiError as e:
                    logger.error(f"Error fetching thread messages: {e.response['error']}")
            

        logger.debug(f"Conversation context: {conversation_context}")

        members_response = client.conversations_members(channel=channel_id)
        if not members_response["ok"]:
            logger.error(f"Failed to retrieve members for channel {channel_id}: {members_response['error']}")
            return
        members = members_response["members"]
        logger.debug(f"Members: {members}")

        logger.debug(f"Using individual prompt template: {individual_prompt}")

        for member in members:
            if member == client.auth_test()["user_id"] or member == "B07HYHHLAFR" or member == "USLACKBOT" or member == "":
                continue
            try:
                member_name = get_user_name(client, member)
                task_start_ts = float(next((m['ts'] for m in conversation if "TO622" in m.get('text', '')), 0))
                task_end_ts = float(next((m['ts'] for m in conversation if "TO243" in m.get('text', '')), float('inf')))

                logger.debug(f"Checking message for user: {msg.get('user')}, member: {member}")
                logger.debug(f"Message timestamp: {float(msg.get('ts', 0))}, Task start: {task_start_ts}, Task end: {task_end_ts}")

                user_context = [
                    msg.get('text') for msg in conversation
                    if (msg.get('user') == member and
                        task_start_ts <= float(msg.get('ts', 0)) <= task_end_ts)
                ]
                formatted_context = user_context + conversation_context
                user_profile = get_user_profile(client, member)
                
                if not user_profile:
                    continue

                client.chat_postEphemeral(
                    channel=channel_id,
                    user=member,
                    text=f"Generating feedback for <@{member}>, please wait..."
                )

                member_messages = []

                for msg in conversation:
                    if msg.get('user') == member and task_start_ts <= float(msg.get('ts', 0)) <= task_end_ts:
                        member_messages.append(msg.get('text', ''))

                    if msg.get('reply_count', 0) > 0:
                        thread_ts = msg['ts']
                        try:
                            thread_messages = client.conversations_replies(channel=channel_id, ts=thread_ts)["messages"]
                            for thread_msg in thread_messages[1:]:
                                if thread_msg.get('user') == member and task_start_ts <= float(thread_msg.get('ts', 0)) <= task_end_ts:
                                    member_messages.append(thread_msg.get('text', ''))
                        except SlackApiError as e:
                            logger.error(f"Error fetching thread messages: {e.response['error']}")

                member_messages = ' '.join(member_messages)
                team_messages = ' '.join([msg.get('text', '') for msg in conversation_context])
                logger.debug(f"Member messages: {member_messages}")
                logger.debug(f"Team messages: {team_messages}")

                member_sentiment = get_team_sentiment(member_messages)
                sentiment_score = member_sentiment['compound']
                sentiment_label = (
                    "positive" if sentiment_score > 0.05
                    else "negative" if sentiment_score < -0.05
                    else "neutral"
                )
                conversation_tuples = [(entry["name"], entry["text"]) for entry in conversation_context]

                lsm_score = LSM(member_messages, team_messages) if member_messages and team_messages else 0
                words_data = words_spoken(conversation_tuples, member_name) if '{words_spoken}' in individual_prompt else {'participant_words': 0, 'percentage': 0}
                format_params = {
                    'speaker': f"{user_profile['real_name']} ({user_profile['title']})",
                    'words_spoken': f"{words_data['participant_words']} words ({words_data['percentage']:.1f}%)" if '{words_spoken}' in individual_prompt else '',
                    'sentiment': f"{sentiment_label} ({sentiment_score:.2f})" if '{sentiment}' in individual_prompt else '',
                    'language_style_matching': f"{lsm_score:.2f}" if '{language_style_matching}' in individual_prompt else '',
                    'team_task': task_description
                }

                logger.debug(f"Calculated metrics for {user_profile['real_name']}:")
                logger.debug(f"Words spoken: {format_params['words_spoken']}")
                logger.debug(f"Sentiment: {format_params['sentiment']}")
                logger.debug(f"LSM Score: {format_params['language_style_matching']}")

                prompt_template = individual_prompt.format(**format_params)


                logger.debug(f"Formatted prompt: {prompt_template}")

                if not prompt_template:
                    logger.error("Prompt template is empty.")
                    return

                response = get_provider_response(
                    client, 
                    member, 
                    selected_model, 
                    channel_id, 
                    prompt_template, 
                    formatted_context
                )
                logger.debug(f"Generated response: {response}")

                client.chat_postEphemeral(
                    channel=channel_id,
                    user=member,
                    text=f"<@{member}>: \n{response}"
                )
                logger.debug(f"Feedback message sent to user {member} in channel {channel_id}")
                
            except Exception as e:
                logger.error(f"Error sending feedback message to user {member}: {e}")
                
        client.chat_postMessage(
            channel=channel_id,
            text=f"BO243 All individual team member feedback generated"
            )

    except Exception as e:
        logger.error(f"Error in app_personal_message: {e}")
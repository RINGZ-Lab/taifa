import json
import logging
from slack_sdk import WebClient
import random
from state_store.get_user_state import get_channel_task

logger = logging.getLogger(__name__)

def create_canvas(client: WebClient, title: str, channel_id: str):
    try:
        team_info = client.team_info()
        if not team_info.get('ok'):
            logger.error("Failed to get team info")
            return None
            
        team_id = team_info['team']['id']
        workspace_url = team_info['team']['domain']

        task_number = get_channel_task(channel_id)
        file_path = f'./task/task{task_number}/task.json'

        try:
            with open(file_path, 'r') as file:
                canvas_data = json.load(file)
                canvas_content = ""
                for section in canvas_data['sections']:
                    canvas_content += f"# {section['title']}\n\n"
                    for item in section['content']:
                        canvas_content += f"- **{item['item']}**: {item['description']}\n"
                    canvas_content += "\n"
        except FileNotFoundError:
            logger.error(f"Canvas content file not found: {file_path}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from file: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading canvas content file: {e}")
            return None

        response = client.canvases_create(
            title=title,
            document_content={
                "type": "markdown",
                "markdown": canvas_content
            }
        )
        
        if response.get('ok'):
            canvas_id = response['canvas_id']
            logger.info(f"Canvas created with ID: {canvas_id}")
            
            canvas_url = f"https://{workspace_url}.slack.com/docs/{team_id}/{canvas_id}"
            
            share_message = client.chat_postMessage(
                channel=channel_id,
                text=f"A new canvas has been created: {canvas_url}",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"@channel Here is your canvas for the current task:\n <{canvas_url}>,\n Click the link to open the task and collaborate with your team.\n Your goal is to discuss and solve the task by ordering the items from most important to least important."
                        }
                    }
                ]
            )
            logger.info(f"Canvas shared: {share_message}")
            access_response = client.canvases_access_set(
                canvas_id=canvas_id,
                access_level="read",
                channel_ids=[channel_id]
            )
            
            if access_response.get('ok'):
                logger.info(f"Canvas access set for channel: {channel_id}")
                return canvas_id
            else:
                logger.error(f"Error setting canvas access: {access_response.get('error')}")
                return None
                
        else:
            logger.error(f"Error creating canvas: {response.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f"Error in canvas creation process: {e}")
        return None

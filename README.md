<div align="center">

 <img src="assets/tAIfa2.png" width="500" alt="tAIfa Icon" />
  
[//]: # (  <h2 style="margin-bottom:0.2em;"> <img src="assets/agent-icon.png" width="20" alt="tAIfa Icon" /> tAIfa</h2> )
[//]: # ()
[//]: # (  <p style="margin-top:0; font-size:1.1em;"><em>Team AI Feedback Assistant</em></p>)



  <!-- Badges: Row 1 -->
  <p>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python"/>
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"/>
    </a>
    <a href="https://slack.com/">
      <img src="https://img.shields.io/badge/Slack-Agent-orange.svg" alt="Slack Agent"/>
    </a>
    <a href="https://azure.microsoft.com/en-us/products/cognitive-services/openai-service/">
      <img src="https://img.shields.io/badge/Azure-OpenAI-blue.svg" alt="Azure OpenAI"/>
    </a>
  </p>


  <!-- Badges: Row 2 -->
  <p>
    <a href="https://arxiv.org/abs/2504.14222">
      <img src="https://img.shields.io/badge/tAIfa-Paper-blueviolet.svg" alt="tAIfa Paper"/>
    </a>
    <a href="https://github.com/RINGZ-Lab/taifa/stargazers">
      <img src="https://img.shields.io/github/stars/RINGZ-Lab/taifa.svg?style=social" alt="GitHub Stars"/>
    </a>
    <a href="https://github.com/RINGZ-Lab/taifa/watchers">
      <img src="https://img.shields.io/github/watchers/RINGZ-Lab/taifa.svg?style=social" alt="GitHub Watchers"/>
    </a>
    <a href="https://github.com/RINGZ-Lab/taifa/network">
      <img src="https://img.shields.io/github/forks/RINGZ-Lab/taifa.svg?style=social" alt="GitHub Forks"/>
    </a>
    <a href="https://github.com/RINGZ-Lab/taifa/issues">
      <img src="https://img.shields.io/github/issues/RINGZ-Lab/taifa.svg" alt="GitHub Issues"/>
    </a>
  </p>
  <hr align="center" width="60%" style="border:0; border-top:1px solid #eee; margin:1em 0;" />

</div>



 ## Overview

**tAIfa** (“Team AI Feedback Assistant”) is a Slack-integrated agent powered by Azure OpenAI. It provides **personalized**, **automated** feedback to both individual members and entire teams by analyzing their conversation dynamics in real time.

## Why tAIfa?

> “We all need people who will give us feedback. That's how we improve.”  
> — Bill Gates, Co-founder of Microsoft

 Timely, actionable feedback is crucial for effective collaboration, learning, and cohesion—yet many teams (especially remote or hybrid) struggle to get feedback that aligns with their goals. tAIfa fills this gap by:
- **Automating** feedback delivery at scale
- **Grounding** suggestions in empirical communication metrics
- **Adapting** to diverse team contexts without pre-existing user data

## Features

- **Automated Analysis** of team chats using seven communication metrics
- **Individual Feedback** delivered as private Slack messages
- **Team Feedback** delivered to the group channel, highlighting collective strengths and areas to improve
- **Lightweight Integration** into existing Slack workspaces
- **Configurable** via environment variables (no additional databases or services required)

### Communication Metrics

tAIfa computes both **text-analytic** and **contextual** metrics to drive feedback:

| Category             | Metric                             | Purpose                                                      |
|----------------------|------------------------------------|--------------------------------------------------------------|
| **Text-Analytic**    | Language Style Matching (LSM)      | Measures linguistic alignment using function-word overlap    |
|                      | Sentiment                          | Assesses emotional tone (–1 to +1)                           |
|                      | Team Engagement                    | Balances word-count contributions                            |
| **Contextual**       | Transactive Memory System (TMS)    | Evaluates recognition of each other’s expertise              |
|                      | Collective Pronouns                | Tracks “we”/“our” usage for shared team identity             |
|                      | Communication Flow                 | Detects interruptions, response delays for interaction health|
|                      | Topic Coherence                    | Checks alignment of discussion with team’s stated goal       |

## Architecture

tAIfa’s consists of **four stages** (see Figure 1 in the paper):

1. **Retrieve & Pre-process**  
   Fetches Slack messages via API, structures them into JSON.

2. **Evaluate Dynamics**  
   Computes the seven communication metrics; embeds them in prompts.

3. **Generate Feedback**  
   Sends structured prompts to the LLM to create individual and team feedback.

4. **Deliver Feedback**  
   Posts private messages to individuals and channel messages to teams.

## Prerequisites

- Python 3.7 or higher
- A Slack App with scopes for reading/writing messages
- Azure OpenAI resource (API key & endpoint)
- (Optional) [Anaconda](https://www.anaconda.com/products/distribution) for env management
- Slack Bot Token & App Token

## Setup Instructions

1 **Create a Virtual Environment**
```bash
# with conda
conda create --name SlackTeamAIFeedback python=3.8  
conda activate SlackTeamAIFeedback  
# or with venv
python -m venv venv  
source venv/bin/activate      # on Windows: venv\Scripts\activate
```

2 **Configure Environment Variables**  
Create a `.env` file in the project root:
```bash
AZURE_API_KEY=your_azure_api_key
AZURE_ENDPOINT=https://<your-azure-name>.openai.azure.com/
AZURE_MODEL_DEPLOYMENT=your_model_name
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_USER_TOKEN=xoxp-...
```

3 **Install Dependencies**
```bash
pip install -r requirements.txt
```

4 **Launch tAIfa**
```bash
python app.py
```

## Usage

Once tAIfa is running, invite the bot to your Slack channel and use the following **slash commands**:

| Command                         | Description                                                         |
|---------------------------------|---------------------------------------------------------------------|
| <code>/distribute_users</code>  | Distributes channel members across one or more channels             |
| <code>/select_prompt &lt;id&gt;</code>   | Chooses tAIfa’s pre-configured feedback templates (IDs 1–9). 
Example:  
• `prompt1` for communication improvement  
• `prompt2` for boosting task efficiency  
You can also supply your own custom prompt text after the ID. |
| <code>/select_tasks &lt;task description&gt;</code> | Defines the team task to consider when generating feedback (e.g. “design sprint”, “bug triage”).                                 |
| <code>/set_timer &lt;seconds&gt;</code>        | Sets how often (in seconds) tAIfa automatically generates feedback in the channel.                                              |

### Model Configuration

By default, tAIfa uses the **o1-preview** model. To switch to another Azure OpenAI model (e.g., **o1-mini**):

1. Open the tAIfa home tab in Slack.
2. Click **Pick an AI Provider**.
3. Select your desired **provider** (Azure) and **model** (o1-mini, etc.).



## Slack App Setup & Permissions

tAIfa needs a few extra permissions in order to read channel history, post feedback, and update profiles. In your Slack App dashboard, go to **OAuth & Permissions** and add the following **Scopes** under **Bot Token Scopes**:

- `users.profile:write`
- `app_mentions:read`
- `channels:history`
- `channels:read`
- `chat:write`
- `chat:write.public`
- `commands`
- `groups:history`
- `groups:read`
- `im:history`
- `im:read`
- `im:write`
- `mpim:history`
- `mpim:read`
- `mpim:write`
- `users:read`

Once you’ve added them:

1. Click **Save Changes**.
2. Scroll up and click **Install to Workspace** (or **Reinstall to Workspace**).
3. Review & **Allow** all the requested permissions.

## Slack App Manifest

tAIfa’s Slack App is fully described by the `manifest.json` in the repo root.  
It includes all the bot scopes, slash-commands, home-tab settings, and event subscriptions needed to run tAIfa.







---
## Citation

If you use **tAIfa** or refer to our work, please cite:

```bibtex
@inproceedings{almutairi2025taifa,
  author    = {Almutairi, Mohammed and Chiang, Charles and Bai, Yuxin and Gomez-Zara, Diego},
  title     = {tAIfa: Team {AI} Feedback Assistant for Enhancing Team Effectiveness in Slack},
  booktitle = {CHIWORK '25: Proceedings of the 4th Annual Symposium on Human-Computer Interaction for Work},
  year      = {2025},
  address   = {Amsterdam, Netherlands},
  publisher = {ACM},
  doi       = {10.1145/3729176.3729197}
}
```

## Acknowledgments

Supported by Slack’s 2024 Workforce Lab Academic Grant Program and Microsoft Research’s Accelerating Foundation Models Research Program.

## Contact

For questions or support, open an issue or email [malmutai@nd.edu](mailto:malmutai@nd.edu).
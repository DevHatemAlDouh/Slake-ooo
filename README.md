<div align="center">

# 💤 Slake-ooo

**A Slack app for scheduling and managing out-of-office status**

[![Platform](https://img.shields.io/badge/Platform-Slack-4A154B?style=flat-square&logo=slack)](https://slack.com/)
[![Language](https://img.shields.io/badge/Language-Python-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-000000?style=flat-square&logo=flask)](https://flask.palletsprojects.com/)
[![Scheduler](https://img.shields.io/badge/Scheduler-APScheduler-2E8B57?style=flat-square)](https://apscheduler.readthedocs.io/)

---

</div>

## 📖 Overview

**Slake-ooo** is a Slack-integrated out-of-office status manager. Use the `/ooo` slash command to connect your account, create OOO entries, and manage your entries and Slack status. The Flask service handles Slack commands and OAuth callbacks, while APScheduler checks entries periodically.

## ✨ Features

- **🗓️ OOO entries:** Record a date, time range, status emoji, and status message. Creating an entry applies its status immediately, with its expiration set to the entry's end time.
- **🔄 Slack status updates:** Apply or clear your Slack profile status.
- **📋 Entry management:** List your entries, remove all your entries, or check their applied state.
- **👥 Account linking:** Connect a Slack account through OAuth or add a user to the app's user list.
- **⏱️ Periodic checks:** Check active, unapplied OOO entries every minute using the `Asia/Aden` timezone.
- **💾 Local persistence:** Store user and OOO entry data in `db.json`; write command activity to `log.log`.

## 🛠️ Tech Stack

| Layer                 | Technology  |
| :-------------------- | :---------- |
| **Language**          | Python      |
| **Web framework**     | Flask       |
| **Slack integration** | Slack SDK   |
| **Scheduler**         | APScheduler |
| **Persistence**       | JSON file   |

## 📂 Project Structure

```text
Slake-ooo/
├── app.py            # Flask routes and /ooo command handling
├── scheduler.py      # OOO entry checks
├── status.py         # Slack profile status updates
├── db.json           # Local user and OOO entry data
├── log.log           # Command activity log
└── requirements.txt  # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or later
- A Slack app configured with a slash command and OAuth redirect URL

Configure the Slack slash command request URL as `https://<your-host>/slack/commands` and the OAuth redirect URL as `https://<your-host>/slack/oauth/callback`.

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/DevHatemAlDouh/Slake-ooo.git
   cd Slake-ooo
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   ```

   On Windows:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   On macOS or Linux:

   ```bash
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** in a `.env` file:

   ```dotenv
   SLACK_CLIENT_ID=your-slack-client-id
   SLACK_CLIENT_SECRET=your-slack-client-secret
   SLACK_REDIRECT_URI=https://your-host/slack/oauth/callback
   SLACK_SIGNING_SECRET=your-slack-signing-secret
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   ```

   Add the scopes required by the app to your Slack app configuration, then install the app in your workspace.

5. **Run the service:**

   ```bash
   python app.py
   ```

   The local service listens on port `5000` by default. Set `PORT` to use a different port.

## 💬 Slash Command Usage

Run these commands in Slack:

| Command                                           | Description                                   |
| :------------------------------------------------ | :-------------------------------------------- |
| `/ooo install`                                    | Get a link to connect your Slack account      |
| `/ooo YYYY-MM-DD HH:MM-HH:MM :emoji: status text` | Create an OOO entry                           |
| `/ooo ooos`                                       | List your OOO entries                         |
| `/ooo clear`                                      | Clear your Slack status                       |
| `/ooo reset`                                      | Remove your OOO entries                       |
| `/ooo whitelist`                                  | Add yourself to the app's user list           |
| `/ooo whitelist @username`                        | Add another Slack user to the app's user list |

Example:

```text
/ooo 2026-12-24 09:00-17:00 :palm_tree: Out of office
```

Times are interpreted using the app's `Asia/Aden` timezone.

## 📝 Data and Configuration

The app reads secrets from environment variables (a local `.env` file is supported) and keeps its records in `db.json`. Do not commit `.env` files or Slack credentials; back up `db.json` if you need to preserve local records.

<!-- {use profolio} -->

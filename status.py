# status.py
import requests
import json

def set_status(user_token, text, emoji, expiration=0):
    profile = {
        "status_text": text,
        "status_emoji": emoji,
        "status_expiration": expiration
    }
    res = requests.post(
        "https://slack.com/api/users.profile.set",
        headers={
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json; charset=utf-8"
        },
        json={"profile": profile}  # send as JSON, not form-data
    )
    data = res.json()
    if not data.get("ok"):
        print("Slack error:", data)
    else:
        print(f"Status set: {text} {emoji} until {expiration}")
    print("Slack response:", data)

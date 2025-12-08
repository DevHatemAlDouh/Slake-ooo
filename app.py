import os
import json
import uuid
from flask import Flask, request, make_response
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler import check_ooo
from status import set_status
from datetime import datetime
from slack_sdk import WebClient

load_dotenv()
app = Flask(__name__)

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
redirect_uri = os.environ["SLACK_REDIRECT_URI"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]
slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

DB_FILE = "db.json"
LOG_FILE = "log.log"

# --- Helpers for JSON persistence ---
def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "ooo_entries": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            # if file accidentally contains a list, wrap it
            return {"users": {}, "ooo_entries": data}
        except json.JSONDecodeError:
            return {"users": {}, "ooo_entries": []}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

def log_command(user_id, command_text,description):
    # print(f"{datetime.now().isoformat()} | User: {user_id} | Command: {command_text} | Description: {description}\n")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | User: {user_id} | Command: {command_text} | Description: {description}\n")

def generate_id():
    return str(uuid.uuid4())

def resolve_username_to_id(username_tag):
    """Resolve @username to Slack user_id using users.list"""
    username = username_tag.lstrip("@")
    print(username)
    resp = slack_client.users_list()
    if not resp["ok"]:
        return None

    for member in resp["members"]:
        if member.get("name") == username or member.get("profile", {}).get("display_name") == username:
            return member["id"]
    return None


# Load existing DB at startup
db = load_db()

# Slack signature verifier
verifier = SignatureVerifier(signing_secret=signing_secret)

@app.route("/slack/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    from requests import post
    resp = post("https://slack.com/api/oauth.v2.access", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }).json()

    if resp.get("ok"):
        user_id = resp["authed_user"]["id"]
        token = resp["authed_user"]["access_token"]

        # ✅ Save user automatically with id + token
        db["users"][user_id] = {
            "id": generate_id(),
            "token": token
        }
        save_db(db)

        print(f"OAuth success: stored token for {user_id}")
        return make_response("App installed! You can now use /ooo", 200)

    print("OAuth error:", resp)
    return make_response(f"Error: {resp}", 400)

@app.route("/slack/commands", methods=["POST"])
def slash_command():
    # Load existing DB at startup
    db = load_db()
    # Verify Slack signature
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid request signature", 403)

    user_id = request.form.get("user_id")
    text = request.form.get("text", "").strip()
    
    # --- INSTALL command ---
    if text.lower().startswith("install"):
        # Fallback if redirect_uri is missing
        redirect = redirect_uri or f"https://yourdomain.com/slack/oauth/callback"

        oauth_url = (
            "https://slack.com/oauth/v2/authorize"
            f"?client_id={client_id}"
            "&scope=commands,users.profile:read,users:read"
            "&user_scope=users.profile:write"
            f"&redirect_uri={redirect_uri}"
        )


        # Check if user already has a token
        user_info = db["users"].get(user_id)
        if user_info and user_info.get("token"):
            log_command(user_id, text,"✅ You're already linked!")
            return make_response(
                f"✅ You're already linked! You can use `/ooo` to schedule your status.",
                200
            )
        log_command(user_id, text,"Click here to install and link")
        return make_response(
        f"🔗 Click here to install and link your account: <{oauth_url}|Install App>",
        200
    )

    # --- CLEAR command ---
    if text.lower().startswith("clear"):
        user_info = db["users"].get(user_id)
        if user_info:
            token = user_info["token"]
            set_status(token, "", "", 0)   # clears status
            print(f"Cleared status for {user_id} ({user_info['id']})")
            log_command(user_id, text,"Your Slack status has been cleared ✅")
            return make_response("Your Slack status has been cleared ✅", 200)
        log_command(user_id, text,"No token found for this user")
        return make_response("No token found for this user", 200)

# --- OOOS command (list all user's OOO entries) ---
    if text.lower().startswith("ooos"):
        user_entries = [e for e in db["ooo_entries"] if e["user_id"] == user_id]

        if not user_entries:
            log_command(user_id, text,"You have no OOO entries scheduled 💤")
            return make_response("You have no OOO entries scheduled 💤", 200)

        # Build a readable list
        lines = []
        for e in user_entries:
            applied_flag = "✅" if e.get("applied") else "⏳"
            lines.append(
                f"- {e['start']} → {e['end']} | {e['status_text']} {e['status_emoji']} {applied_flag}"
            )

        response_text = "📋 Your OOO entries:\n" + "\n".join(lines)
        log_command(user_id, text,response_text)
        return make_response(response_text, 200)

    # --- RESET command (wipe all OOO entries) ---
    if text.lower().startswith("reset"):
        before_count = len(db["ooo_entries"])
        # keep only entries that do NOT belong to this user
        db["ooo_entries"] = [e for e in db["ooo_entries"] if e["user_id"] != user_id]
        after_count = len(db["ooo_entries"])
        save_db(db)

        cleared = before_count - after_count
        print(f"User {user_id} cleared {cleared} OOO entries")
        log_command(user_id, text,f"Your OOO entries have been cleared 🗑️ ({cleared} removed)")
        return make_response(f"Your OOO entries have been cleared 🗑️ ({cleared} removed)", 200)

    # --- WHITELIST command ---
    if text.lower().startswith("whitelist"):
        parts = text.split()
        if len(parts) == 1:
            target_user_id = user_id
        elif len(parts) == 2 and parts[1].startswith("@"):
            target_user_id = resolve_username_to_id(parts[1])
            if not target_user_id:
                log_command(user_id, text,f"Could not resolve {parts[1]} ❌")
                return make_response(f"Could not resolve {parts[1]} ❌", 200)
        else:
            log_command(user_id, text,"Usage: /ooo whitelist or /ooo whitelist @user")
            return make_response("Usage: /ooo whitelist or /ooo whitelist @user", 200)

        if target_user_id in db["users"]:
            log_command(user_id, text,f"User <@{target_user_id}> is already whitelisted ✅")
            return make_response(f"User <@{target_user_id}> is already whitelisted ✅", 200)

        db["users"][target_user_id] = {"id": generate_id(), "token": ""}
        save_db(db)
        print(f"User {target_user_id} whitelisted by {user_id}")
        log_command(user_id, text,f"User <@{target_user_id}> added to whitelist 📝")
        return make_response(f"User <@{target_user_id}> added to whitelist 📝", 200)

    # --- OOO scheduling ---
    parts = text.split()
    if len(parts) < 4:
        print(text)
        return make_response("Format: YYYY-MM-DD HH:MM-HH:MM :emoji: status_text", 200)

    date = parts[0]
    times = parts[1]
    emoji = parts[2]
    status_text = " ".join(parts[3:])

    try:
        start_time, end_time = times.split("-")
    except ValueError:
        return make_response("Time must be in HH:MM-HH:MM format", 200)

    # Normalize times
    try:
        start_fmt = datetime.strptime(start_time, "%H:%M").strftime("%H:%M:%S")
        end_fmt = datetime.strptime(end_time, "%H:%M").strftime("%H:%M:%S")
    except ValueError:
        return make_response("Invalid time format, use HH:MM", 200)

    start_iso = f"{date}T{start_fmt}"
    end_iso = f"{date}T{end_fmt}"

    # Prevent duplicates
    for e in db["ooo_entries"]:
        if e["user_id"] == user_id and e["start"] == start_iso and e["end"] == end_iso:
            return make_response("An OOO entry already exists for this time.", 200)

    entry = {
        "id": generate_id(),
        "user_id": user_id,
        "start": start_iso,
        "end": end_iso,
        "status_text": status_text,
        "status_emoji": emoji,
        "applied": False
    }
    
    db["ooo_entries"].append(entry)
    save_db(db)

    # 🔑 Apply status right now
    user_info = db["users"].get(user_id)
    if user_info:
        token = user_info["token"]
        expiration = int(datetime.strptime(end_iso, "%Y-%m-%dT%H:%M:%S").timestamp())
        set_status(token, status_text, emoji, expiration)
        entry["applied"] = True
        save_db(db)
        print(f"Applied OOO for {user_id} ({user_info['id']}): {status_text} {emoji}")

    return make_response(
        f"OOO scheduled & applied: {date} {start_time}-{end_time} | {status_text} {emoji}",
        200
    )

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: check_ooo(db["users"], db["ooo_entries"]), "interval", minutes=1)
    scheduler.start()
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)

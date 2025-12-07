# scheduler.py (FIXED)
from datetime import datetime
import pytz
from status import set_status

def check_ooo(users, ooo_entries):
    tz = pytz.timezone("Asia/Aden")
    now = datetime.now(tz)

    entries_to_keep = []
    dirty = False

    for entry in ooo_entries:
        # Parse naive ISO string and attach timezone
        try:
            start = datetime.fromisoformat(entry["start"]).replace(tzinfo=tz)
            end = datetime.fromisoformat(entry["end"]).replace(tzinfo=tz)
        except ValueError:
             print(f"Error parsing dates for entry {entry['id']}, skipping.")
             entries_to_keep.append(entry)
             continue

        user_id = entry["user_id"]
        
        # --- FIX STARTS HERE ---
        user_data = users.get(user_id)
        if not user_data or "token" not in user_data:
             print(f"No token found for user {user_id}, skipping.")
             entries_to_keep.append(entry)
             continue
        token = user_data["token"]
        # --- FIX ENDS HERE ---

        # Apply status if within window
        if start <= now <= end and not entry.get("applied", False):
            expiration = int(end.timestamp())
            set_status(token, entry["status_text"], entry["status_emoji"], expiration)
            entry["applied"] = True
            dirty = True
            print(f"Applied OOO for {user_id}: {entry['status_text']} {entry['status_emoji']}")

        # Mark as done if past end
        if now > end:
            if entry.get("applied", False):
                 # Optional: You could force clear status here just in case
                 # set_status(token, "", "", 0) 
                 print(f"Finished OOO for {user_id}")
            entry["done"] = True
            dirty = True
        
        if not entry.get("done"):
             entries_to_keep.append(entry)

    # Clean up finished entries safely
    if dirty:
         ooo_entries[:] = entries_to_keep
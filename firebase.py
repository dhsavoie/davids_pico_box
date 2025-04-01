import network
import urequests
import ujson
import time
import machine

from my_secrets import FIREBASE_URL

def check_messages():
    try:
        response = urequests.get(FIREBASE_URL)
        messages = response.json()
        response.close()
        
        if messages:
            for msg_id, msg_data in messages.items():
                if not msg_data.get("read", False):  # Only process unread messages
                    print("New message:", msg_data["text"])
                    
                    # Mark message as read
                    mark_message_as_read(msg_id)

                    return msg_data["text"]
                else:
                    return None
        else:
            return None
    except Exception as e:
        print("Error fetching messages:", e)
        return None

def mark_message_as_read(msg_id):
    update_url = f"{FIREBASE_URL[:-5]}/{msg_id}.json"
    update_data = ujson.dumps({"read": True})
    try:
        urequests.patch(update_url, data=update_data)
        print(f"Marked {msg_id} as read.")
    except Exception as e:
        print("Error updating message:", e)
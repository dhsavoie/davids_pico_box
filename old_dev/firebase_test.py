import network
import urequests
import ujson
import time
from my_secrets import network_name, password, FIREBASE_URL

# WiFi credentials (you might have this set up already)
SSID = network_name
PASSWORD = password


# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)

print("Connected to WiFi!")

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
    except Exception as e:
        print("Error fetching messages:", e)

def mark_message_as_read(msg_id):
    update_url = f"{FIREBASE_URL[:-5]}/{msg_id}.json"  # Remove .json from the URL
    update_data = ujson.dumps({"read": True})
    try:
        urequests.patch(update_url, data=update_data)
        print(f"Marked {msg_id} as read.")
    except Exception as e:
        print("Error updating message:", e)

while True:
    check_messages()
    time.sleep(5)  # Check every 5 seconds

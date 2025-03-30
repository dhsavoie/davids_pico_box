from lcd import LCD
import network
import urequests
import ujson
import time
import machine

from my_secrets import FIREBASE_URL

lcd = LCD(rs=13, e=12, d4=11, d5=10, d6=9, d7=8)

def check_messages():
    try:
        response = urequests.get(FIREBASE_URL)
        messages = response.json()
        response.close()
        
        if messages:
            for msg_id, msg_data in messages.items():
                if not msg_data.get("read", False):  # Only process unread messages
                    print("New message:", msg_data["text"])
                    lcd.clear()
                    lcd.write(msg_data["text"])
                    
                    # Mark message as read
                    mark_message_as_read(msg_id)
    except Exception as e:
        print("Error fetching messages:", e)

def mark_message_as_read(msg_id):
    update_url = f"{FIREBASE_URL[:-5]}/{msg_id}.json"
    update_data = ujson.dumps({"read": True})
    try:
        urequests.patch(update_url, data=update_data)
        print(f"Marked {msg_id} as read.")
    except Exception as e:
        print("Error updating message:", e)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

lcd.clear()
lcd.write("Inside test!")
time.sleep(10)

while True:
    if not wlan.isconnected():
        lcd.clear()
        lcd.write("Reconnecting...")
        machine.reset()
    
    check_messages()
    time.sleep(5)
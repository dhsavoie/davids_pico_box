import time
import ujson
import socket
import network
import framebuf
import urequests
import micropython
from sh1106 import *
# from firebase import *
from oled_graphics import *
from machine import Pin, I2C
from captive_portal import *
from connect_to_wifi import *
from my_secrets import pico_AP, pico_AP_pw, FIREBASE_URL, owner

debounce_delay = 500
last_press_time = 0

unopened_messages = []
new_message_waiting = False
envelope_open = False
current_message_index = 0

button = Pin(0, Pin.IN, Pin.PULL_UP)

def check_messages():
    # unopened_messages = []
    global unopened_messages, new_message_waiting
    try:
        response = urequests.get(FIREBASE_URL)
        messages = response.json()
        response.close()

        if messages:
            for msg_id, msg_data in messages.items():
                if msg_data.get("sender") != owner:
                    if not msg_data.get("read", False):  # Only process unread messages
                        print(f"New message from {msg_data['sender']}: {msg_data['text']}")
                        unopened_messages.append(msg_data["text"])
                        # Mark message as read
                        mark_message_as_read(msg_id)

        if unopened_messages:
            new_message_waiting = True
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

def handle_button_press(pin):
    global current_message_index, new_message_waiting, unopened_messages, last_press_time, envelope_open

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > debounce_delay:
        last_press_time = current_time  # Update last press time
        
        if new_message_waiting and unopened_messages:
            # Display current message
            envelope_open = False
            display.display_wrapped_text(unopened_messages[current_message_index])
            display.fill_rect(0, 64-8, 8, 8, 0)
            display.text(f"{current_message_index+1}/{len(unopened_messages)}", 0, 64-8, 1)
            display.show()

            # Move to next message
            current_message_index += 1

            # If we reached the end of the queue, reset
            if current_message_index >= len(unopened_messages):
                unopened_messages = []  # Clear queue
                current_message_index = 0
                new_message_waiting = False  # No more messages waiting



i2c = I2C(1, sda=Pin(18), scl=Pin(19), freq=400000)
display = SH1106_I2C(128, 64, i2c, rotate=180)
display.fill(0)  # Clear the display

button.irq(trigger=Pin.IRQ_FALLING, handler=handle_button_press)

# first check if wifi credentials are saved
if not connect_to_wifi():
    display.display_wrapped_text("Starting AP. Connect to PicoSetup, password 12345678")
    captive_portal()
else:
    display.display_wrapped_text("Connected to WiFi!")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    previous_length = 0
    while True:
        if not wlan.isconnected():
            machine.reset()
        
        check_messages()
        if new_message_waiting:
            if len(unopened_messages) > 0:
                if previous_length == 0:
                    display.fill(0)
                    display.new_message_envelope()
                    envelope_open = True
                    display.text(f"{len(unopened_messages)}", 8, 64-8, 1)
                    display.show()
                elif envelope_open:
                    if previous_length != len(unopened_messages):
                        display.fill_rect(8, 64-8, 8, 8, 0)
                        display.text(f"{len(unopened_messages)}", 8, 64-8, 1)
                        display.show()
        previous_length = len(unopened_messages)

        time.sleep(5)

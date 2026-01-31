import gc
import time
import ujson
import socket
import network
import framebuf
import urequests
import micropython
from sh1106 import *
from logging import *
from oled_graphics import *
from machine import Pin, I2C
from captive_portal import *
from connect_to_wifi import *
from my_secrets import pico_AP, pico_AP_pw, FIREBASE_MESSAGES_URL, FIREBASE_HEART_URL, owner, receiver

DEBOUNCE_DELAY = 500
last_press_time = 0

POLLING_DELAY = 3  # seconds
MAX_RECONNECT_ATTEMPTS = 5
MESSAGE_QUERY_LIMIT = 10 # limit query so we only pull last 10 entries

unopened_messages = []
opened_messages = []
new_message_waiting = False
envelope_open = False
current_message_index = 0
opened_message_index = 0

heart_state = "full"

scroll_button = Pin(0, Pin.IN, Pin.PULL_UP)
heart_button = Pin(1, Pin.IN, Pin.PULL_UP)

def check_messages():
    # unopened_messages = []
    global unopened_messages, new_message_waiting, opened_messages, opened_message_index
    try:
        response = urequests.get(FIREBASE_MESSAGES_URL + f'?orderBy="$key"&limitToLast={MESSAGE_QUERY_LIMIT}')
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
            opened_messages = []
            opened_message_index = 0
    except Exception as e:
        print("Error fetching messages:", e)

def check_heart():
    global envelope_open, heart_state
    # gc.collect()
    try:
        response = urequests.get(FIREBASE_HEART_URL)
        heart = response.json()
        response.close()

        if heart:
            for heart_id, heart_data in heart.items():
                if heart_data.get("owner") == owner and not envelope_open:
                    # fb = framebuf.FrameBuffer(small_full_heart, 16, 8, framebuf.MONO_HLSB)
                    display.blit(display.fb_small_full_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                    display.show()
                    heart_state = "full"
                elif heart_data.get("owner") == receiver and not envelope_open:
                    # fb = framebuf.FrameBuffer(small_empty_heart, 16, 8, framebuf.MONO_HLSB)
                    display.blit(display.fb_small_empty_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                    display.show()
                    heart_state = "empty"
    except Exception as e:
        print("Error fetching heart:", e)

def mark_message_as_read(msg_id):
    update_url = f"{FIREBASE_MESSAGES_URL[:-5]}/{msg_id}.json"
    update_data = ujson.dumps({"read": True})
    try:
        urequests.patch(update_url, data=update_data)
        print(f"Marked {msg_id} as read.")
    except Exception as e:
        print("Error updating message:", e)

def handle_button_press(pin):
    global current_message_index, new_message_waiting, unopened_messages, last_press_time, envelope_open, opened_messages, opened_message_index

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > DEBOUNCE_DELAY:
        last_press_time = current_time  # Update last press time
        
        if new_message_waiting and unopened_messages:
            # Display current message
            envelope_open = False
            display.display_wrapped_text(unopened_messages[current_message_index])
            display.fill_rect(0, 64-8, 8, 8, 0)
            display.text(f"{current_message_index+1}/{len(unopened_messages)}", 0, 64-8, 1)
            display.show()
            opened_messages.append(unopened_messages[current_message_index])

            # Move to next message
            current_message_index += 1

            # If we reached the end of the queue, reset
            if current_message_index >= len(unopened_messages):
                unopened_messages = []  # Clear queue
                opened_message_index = current_message_index
                current_message_index = 0
                new_message_waiting = False  # No more messages waiting
        else:
            opened_message_index += 1
            if opened_message_index >= len(opened_messages):
                opened_message_index = 0
            display.display_wrapped_text(opened_messages[opened_message_index])
            display.fill_rect(0, 64-8, 8, 8, 0)
            display.text(f"{opened_message_index+1}/{len(opened_messages)}", 0, 64-8, 1)
            display.show()

def handle_pass_heart(pin):
    global heart_state, last_press_time, envelope_open

    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_press_time) > DEBOUNCE_DELAY:
        last_press_time = current_time  # Update last press time

        if heart_state == "full":
            heart_state = "empty"
            if not envelope_open:
                # fb = framebuf.FrameBuffer(small_empty_heart, 16, 8, framebuf.MONO_HLSB)
                display.blit(display.fb_small_empty_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                display.show()

            update_url = f"{FIREBASE_HEART_URL[:-5]}/heart.json"
            update_data = ujson.dumps({"owner": receiver})
            try:
                urequests.patch(update_url, data=update_data)
            except Exception as e:
                print("Error updating heart:", e)

            



i2c = I2C(1, sda=Pin(18), scl=Pin(19), freq=400000)
display = SH1106_I2C(128, 64, i2c, rotate=180)
display.fill(0)  # Clear the display

scroll_button.irq(trigger=Pin.IRQ_FALLING, handler=handle_button_press)
heart_button.irq(trigger=Pin.IRQ_FALLING, handler=handle_pass_heart)

print("old main")
# first check if wifi credentials are saved
wlan = connect_to_wifi()
if not wlan:
    display.display_wrapped_text(f"Connect to wifi {pico_AP}, password {pico_AP_pw}, then enter wifi info at http:// 192.168.4.1")
    log("Opening captive portal")
    captive_portal()
else:
    display.display_wrapped_text("Connected to WiFi!")
    log("Connected to wifi!")

    previous_length = 0
    reconnect_attempts = 0
    while True:
        if not wlan.isconnected():
            reconnect = reconnect_wifi(wlan)
            if reconnect:
                reconnect_attempts = 0
            else:
                reconnect_attempts += 1
        else:
        
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

            check_heart()

        if reconnect_attempts == MAX_RECONNECT_ATTEMPTS:
            display.display_wrapped_text("Could not reconnect to wifi. Please restart!")
            log(f"Failed to reconnect to wifi after {MAX_RECONNECT_ATTEMPTS}")
        time.sleep(POLLING_DELAY)

import gc
import time
import ujson
import framebuf
import urequests
from wifi import *
from sh1106 import *
from logging import *
from oled_graphics import *
from machine import Pin, I2C
from captive_portal import *
from my_secrets import pico_AP, pico_AP_pw, FIREBASE_MESSAGES_URL, FIREBASE_HEART_URL, owner, receiver

##### CONSTANTS #####
DEBOUNCE_DELAY_MS       = 500
POLLING_DELAY_S         = 3
MAX_RECONNECT_ATTEMPTS  = 5
MESSAGE_QUERY_LIMIT     = 10

##### HARDWARE DEFINITIONS #####
scroll_button   = Pin(0,Pin.IN,Pin.PULL_UP)
heart_button    = Pin(1,Pin.IN,Pin.PULL_UP)
i2c             = I2C(1,sda=Pin(18),scl=Pin(19),freq=400000)
display         = SH1106_I2C(128,64,i2c,rotate=180)

class Box:
    def __init__(self, display):
        self.unopened_messages          = []
        self.opened_messages            = []
        self.new_message_waiting        = False
        self.envelope_open              = False
        self.current_message_index      = 0
        self.opened_message_index       = 0
        self.heart_state                = 1 # 1 means full, 0 means empty
        self.last_press_time_scroll     = 0
        self.last_press_time_heart      = 0
        self.display = display

    def check_messages(self):
        try:
            gc.collect()
            response = urequests.get(FIREBASE_MESSAGES_URL + f'?orderBy="$key"&limitToLast={MESSAGE_QUERY_LIMIT}')
            messages = response.json()
            response.close()
            response = None
            gc.collect()

            if messages:
                for msg_id, msg_data in messages.items():
                    if msg_data.get('sender') != owner:
                        if not msg_data.get('read', False):
                            print(f"New message from {msg_data['sender']}: {msg_data['text']}")
                            self.unopened_messages.append(msg_data['text'])
                            self._mark_message_as_read(msg_id)

            if self.unopened_messages:
                self.new_message_waiting = True
                self.opened_messages = []
                self.opened_message_index = 0
        except Exception as e:
            print("Error fetching messages:", e)

    def check_heart(self):
        try:
            gc.collect()
            response = urequests.get(FIREBASE_HEART_URL)
            heart = response.json()
            response.close()
            response = None
            gc.collect()

            if heart:
                for heart_id, heart_data in heart.items():
                    if heart_data.get('owner') == owner and not self.envelope_open:
                        self.display.blit(self.display.fb_small_full_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                        self.display.show()
                        gc.collect()
                        self.heart_state = 1
                    elif heart_data.get('owner') == receiver and not self.envelope_open:
                        self.display.blit(self.display.fb_small_empty_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                        self.display.show()
                        gc.collect()
                        self.heart_state = 0
        except Exception as e:
            print("Error fetching heart:", e)

    def _mark_message_as_read(self, msg_id):
        update_url = f"{FIREBASE_MESSAGES_URL[:-5]}/{msg_id}.json"
        update_data = ujson.dumps({'read': True})
        try:
            urequests.patch(update_url, data=update_data)
            print(f"Marked {msg_id} as read.")
        except Exception as e:
            print("Error updating message:", e)

    def handle_button_press(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_press_time_scroll) > DEBOUNCE_DELAY_MS:
            self.last_press_time_scroll = current_time

            if self.new_message_waiting and self.unopened_messages:
                # display current message
                self.envelope_open = False
                self.display.display_wrapped_text(self.unopened_messages[self.current_message_index])
                self.display.fill_rect(0, 64-8, 8, 8, 0)
                self.display.text(f"{self.current_message_index+1}/{len(self.unopened_messages)}", 0, 64-8, 1)
                self.display.show()
                self.opened_messages.append(self.unopened_messages[self.current_message_index])

                # move to next message
                self.current_message_index += 1

                # if we reached end of the queue, reset
                if self.current_message_index >= len(self.unopened_messages):
                    self.unopened_messages = [] # clear queue
                    self.opened_message_index = self.current_message_index
                    self.current_message_index = 0
                    self.new_message_waiting = False
            else:
                self.opened_message_index += 1
                if self.opened_message_index >= len(self.opened_messages):
                    self.opened_message_index = 0
                self.display.display_wrapped_text(self.opened_messages[self.opened_message_index])
                self.display.fill_rect(0, 64-8, 8, 8, 0)
                self.display.text(f"{self.opened_message_index+1}/{len(self.opened_messages)}", 0, 64-8, 1)
                self.display.show()

    def handle_pass_heart(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_press_time_heart) > DEBOUNCE_DELAY_MS:
            self.last_press_time_heart = current_time

            if self.heart_state == 1:
                self.heart_state = 0
                if not self.envelope_open:
                    fb = framebuf.FrameBuffer(small_empty_heart, 16, 8, framebuf.MONO_HLSB)
                    self.display.blit(self.display.fb_small_empty_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                    self.display.show()

                update_url = f"{FIREBASE_HEART_URL[:-5]}/heart.json"
                update_data = ujson.dumps({'owner': receiver})
                try:
                    urequests.patch(update_url, data=update_data)
                except Exception as e:
                    print("Error updating heart:", e)
                







##### MAIN CODE #####
print("running new main")

box = Box(display)

# assign interrupts
scroll_button.  irq(trigger=Pin.IRQ_FALLING,handler=box.handle_button_press)
heart_button.   irq(trigger=Pin.IRQ_FALLING,handler=box.handle_pass_heart)

# clear display
display.fill(0)

# Wifi Connection
wlan = connect_to_wifi()
if not wlan:
    display.display_wrapped_text(f"Connect to wifi {pico_AP}, password {pico_AP_pw}, then enter wifi info at http:// 192.168.4.1")
    log("Opening captive portal")
    captive_portal()
else:
    display.display_wrapped_text("Connected to WiFi!")
    log("Connected to WiFi!")

    reconnect_attempts = 0
    prev_length = 0

    # Loop
    while True:
        if not wlan.isconnected():
            reconnect = reconnect_wifi(wlan)
            if reconnect:
                reconnect_attempts = 0
            else:
                reconnect_attempts += 1
        else:
            
            box.check_messages()
            if box.new_message_waiting:
                if len(box.unopened_messages) > 0:
                    if prev_length == 0:
                        display.fill(0)
                        display.new_message_envelope()
                        box.envelope_open = True
                        display.text(f"{len(box.unopened_messages)}", 8, 64-8, 1)
                        display.show()
                        gc.collect()
                    elif box.envelope_open:
                        if prev_length != len(box.unopened_messages):
                            display.fill_rect(8, 64-8, 8, 8, 0)
                            display.text(f"{len(box.unopened_messages)}", 8, 64-8, 1)
                            display.show()
                            gc.collect()
            prev_length = len(box.unopened_messages)

            box.check_heart()

        if reconnect_attempts == MAX_RECONNECT_ATTEMPTS:
            display.display_wrapped_text("Could not reconnect to wifi. Please restart!")
            log(f"Failed to reconnect to wifi after {MAX_RECONNECT_ATTEMPTS}")

        time.sleep(POLLING_DELAY_S)

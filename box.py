import gc
import time
import ujson
import framebuf
import urequests

from my_secrets import *

##### CONSTANTS #####
MESSAGE_QUERY_LIMIT     = 6
DEBOUNCE_DELAY_MS       = 500

##### CLASS #####
class Box:
    """This is a class which takes care of button handling and database requests for the Pico Box"""
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

    """Check messages from the database and store unread messages from right sender"""
    def check_messages(self):
        try:
            # garbage collection to avoid mem issues
            gc.collect()
            # json database request
            response = urequests.get(FIREBASE_MESSAGES_URL + f'?orderBy="$key"&limitToLast={MESSAGE_QUERY_LIMIT}')
            messages = response.json()
            response.close()
            response = None
            gc.collect()

            # if messages found, parse and add to unopened messages if unread and by correct sender
            if messages:
                for msg_id, msg_data in messages.items():
                    if msg_data.get('sender') != owner:
                        if not msg_data.get('read', False):
                            print(f"New message from {msg_data['sender']}: {msg_data['text']}")
                            self.unopened_messages.append(msg_data['text'])
                            self._mark_message_as_read(msg_id)

            # if there were unopened messages, set waiting message state to true
            if self.unopened_messages:
                self.new_message_waiting = True
                self.opened_messages = []
                self.opened_message_index = 0
        except Exception as e:
            print("Error fetching messages:", e)

    """Check the ownership of the heart"""
    def check_heart(self):
        try:
            # garbage collection to avoid mem issues
            gc.collect()
            # json database request
            response = urequests.get(FIREBASE_HEART_URL)
            heart = response.json()
            response.close()
            response = None
            gc.collect()

            # if json found, display heart as full if listed owner matches true owner, display empty if not
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

    """Send json to mark a message as read after it has been displayed"""
    def _mark_message_as_read(self, msg_id):
        update_url = f"{FIREBASE_MESSAGES_URL[:-5]}/{msg_id}.json"
        update_data = ujson.dumps({'read': True})
        try:
            urequests.patch(update_url, data=update_data)
            print(f"Marked {msg_id} as read.")
        except Exception as e:
            print("Error updating message:", e)

    #Todo: need to dive into this and improve it and also understand it
    """On scroll button press, open and cycle through messages"""
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

    """On heart button press, send json to change heart ownership"""
    def handle_pass_heart(self, pin):
        # check time to debounce button
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_press_time_heart) > DEBOUNCE_DELAY_MS:
            self.last_press_time_heart = current_time

            # only act if heart is full when button is pressed
            if self.heart_state == 1:
                # change state from full to empty
                self.heart_state = 0

                # if not displaying envelope, change display to match state
                if not self.envelope_open:
                    self.display.blit(self.display.fb_small_empty_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                    self.display.show()

                # update database to reflect true ownership
                update_url = f"{FIREBASE_HEART_URL[:-5]}/heart.json"
                update_data = ujson.dumps({'owner': receiver})
                
                try:
                    urequests.patch(update_url, data=update_data)
                except Exception as e:
                    print("Error updating heart:", e)
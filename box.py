import gc
import time
import ujson
import framebuf
import urequests

from my_secrets import *

##### CONSTANTS #####
MESSAGE_QUERY_LIMIT     = 6
DEBOUNCE_DELAY_MS       = 500

##### STATE CLASSES #####
class State:
    INITIAL                 = 0
    NEW_MESSAGE_WAITING     = 1
    ENVELOPE_OPEN           = 2
    DISPLAYING_MESSAGE      = 3

class HeartState:
    EMPTY   = 0
    FULL    = 1
    
##### CLASS #####
class Box:
    """This is a class which takes care of button handling and database requests for the Pico Box"""
    def __init__(self, display):
        self.message_queue              = []
        self.current_message_index      = 0
        self.prev_queue_length          = len(self.message_queue)

        self.heart_state                = HeartState.FULL

        self.last_press_time_scroll     = 0
        self.last_press_time_heart      = 0
        
        self.display                    = display

        self.state                      = State.INITIAL
        self.prev_state                 = State.INITIAL

    """Change the current state and save the previous state"""
    def set_state(self, new_state):
        self.prev_state = self.state
        self.state = new_state

    """Check for new messages"""
    def check_messages(self):
        try:
            # garbage collect to free unused memory
            gc.collect()
            # query firebase realtime database for last <x> messages
            response = urequests.get(FIREBASE_MESSAGES_URL + f'?orderBy="$key"&limitToLast={MESSAGE_QUERY_LIMIT}')
            messages = response.json()
            response.close()
            response = None
            gc.collect()

            # if query successful...
            if messages:
                # iterate through messages to look for correct sender and read status
                for msg_id, msg_data in messages.items():
                    sender = msg_data.get('sender')
                    read_status = msg_data.get('read', False)

                    # if there is an unread message...
                    if (sender != owner) and (not read_status):

                        # if we are currently displaying messages...
                        if self.state == State.DISPLAYING_MESSAGE:
                            # clear queue as well as length and index variables
                            self.message_queue = []
                            self.prev_queue_length = len(self.message_queue)
                            self.current_message_index = 0

                        # add new message to the queue and mark it as read in firebase
                        message = msg_data['text']
                        print(f"New message from {sender}: {message}")
                        self.message_queue.append(message)
                        self._mark_message_as_read(msg_id)
            
            # if there was a new message, change state to indicate new message is waiting
            if len(self.message_queue) > self.prev_queue_length:
                print(self.message_queue)
                self.prev_queue_length = len(self.message_queue)
                self.set_state(State.NEW_MESSAGE_WAITING) # update state

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
                    if (heart_data.get('owner') == owner) and (self.state != State.ENVELOPE_OPEN):
                        self.display.blit(self.display.fb_small_full_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                        self.display.show()
                        gc.collect()
                        self.heart_state = HeartState.FULL
                    elif (heart_data.get('owner') == receiver) and (self.state != State.ENVELOPE_OPEN):
                        self.display.blit(self.display.fb_small_empty_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                        self.display.show()
                        gc.collect()
                        self.heart_state = HeartState.EMPTY
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

    """On scroll button press, open and cycle through messages"""
    def handle_button_press(self, pin):
        # button debounce mechanism
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_press_time_scroll) > DEBOUNCE_DELAY_MS:
            self.last_press_time_scroll = current_time

            # if the envelope is currently being displayed, clear it and display first message in the message queue
            if self.state == State.ENVELOPE_OPEN:
                self.set_state(State.DISPLAYING_MESSAGE)
                self.display.display_wrapped_text(self.message_queue[self.current_message_index])
                self.display.fill_rect(0, 64-8, 8, 8, 0)
                self.display.text(f"{self.current_message_index+1}/{len(self.message_queue)}", 0, 64-8, 1)
                self.display.show()

            # if already displaying a message, cycle through messages in message queue
            elif self.state == State.DISPLAYING_MESSAGE:
                self.current_message_index += 1

                # if the index exceeds the length of the queue, wrap back around to 0
                if (self.current_message_index + 1) > len(self.message_queue):
                    self.current_message_index = 0

                # display message of current index
                self.display.display_wrapped_text(self.message_queue[self.current_message_index])
                self.display.fill_rect(0, 64-8, 8, 8, 0)
                self.display.text(f"{self.current_message_index+1}/{len(self.message_queue)}", 0, 64-8, 1)
                self.display.show()


    """On heart button press, send json to change heart ownership"""
    def handle_pass_heart(self, pin):
        # button debounce mechanism
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_press_time_heart) > DEBOUNCE_DELAY_MS:
            self.last_press_time_heart = current_time

            # only act if heart is full when button is pressed
            if self.heart_state == HeartState.FULL:
                # change state from full to empty
                self.heart_state = HeartState.EMPTY

                # if not displaying envelope, change display to match state
                if self.state != State.ENVELOPE_OPEN:
                    self.display.blit(self.display.fb_small_empty_heart, 128-16, 64-8, framebuf.MONO_HLSB)
                    self.display.show()

                # update database to reflect true ownership
                update_url = f"{FIREBASE_HEART_URL[:-5]}/heart.json"
                update_data = ujson.dumps({'owner': receiver})
                
                try:
                    urequests.patch(update_url, data=update_data)
                except Exception as e:
                    print("Error updating heart:", e)
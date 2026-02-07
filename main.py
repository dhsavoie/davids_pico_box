import gc
import time

from box            import Box, State
from wifi           import *
from sh1106         import *
from machine        import Pin, I2C
from logging        import *
from my_secrets     import *
from oled_graphics  import *
from captive_portal import *


##### CONSTANTS #####
POLLING_DELAY_S         = 3
MAX_RECONNECT_ATTEMPTS  = 5

##### HARDWARE DEFINITIONS #####
scroll_button   = Pin(0,Pin.IN,Pin.PULL_UP)
heart_button    = Pin(1,Pin.IN,Pin.PULL_UP)
i2c             = I2C(1,sda=Pin(18),scl=Pin(19),freq=400000)
display         = SH1106_I2C(128,64,i2c,rotate=180)
               

##### MAIN CODE #####
print("running scroll fix")

# instantiate box object
box = Box(display)

# assign interrupts
scroll_button.  irq(trigger=Pin.IRQ_FALLING,handler=box.handle_button_press)
heart_button.   irq(trigger=Pin.IRQ_FALLING,handler=box.handle_pass_heart)

# clear display
display.fill(0)

# Wifi Connection
wlan = None
gc.collect()
wlan = connect_to_wifi()
# if connection not successful, prompt for captive portal
if not wlan:
    display.display_wrapped_text(f"Connect to wifi {pico_AP}, password {pico_AP_pw}, then enter wifi info at http:// 192.168.4.1")
    log("Opening captive portal")
    captive_portal()
else:
    display.display_wrapped_text("Connected to WiFi!")
    log("Connected to WiFi!")
    time.sleep(2)

    # track reconnect attempts
    reconnect_attempts = 0

    # main loop
    while True:
        # check connection and attempt to reconnect if connection lost
        if not wlan.isconnected():
            reconnect = reconnect_wifi(wlan)
            if reconnect:
                reconnect_attempts = 0
            else:
                reconnect_attempts += 1
        else:
            # check messages for new messages
            box.check_messages()

            # if state indicates a new message has arrived, display envelope and show num of messages
            if box.state == State.NEW_MESSAGE_WAITING:
                display.fill(0)
                display.new_message_envelope()
                box.set_state(State.ENVELOPE_OPEN) # update state
                display.text(f"{len(box.message_queue)}", 8, 64-8, 1)
                display.show()
                gc.collect()

            # check heart ownership and update heart graphic
            box.check_heart()

        # timeout after some amount of reconnect attempts
        if reconnect_attempts == MAX_RECONNECT_ATTEMPTS:
            display.display_wrapped_text("Could not reconnect to wifi. Please restart!")
            log(f"Failed to reconnect to wifi after {MAX_RECONNECT_ATTEMPTS}")
            break

        time.sleep(POLLING_DELAY_S)
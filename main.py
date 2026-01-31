import gc
import time

from box            import Box
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
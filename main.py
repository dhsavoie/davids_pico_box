import time
import socket
import network
import framebuf
from oled import *
from sh1106 import *
from firebase import *
from machine import Pin, I2C
from captive_portal import *
from connect_to_wifi import *
from my_secrets import pico_AP, pico_AP_pw

i2c = I2C(1, sda=Pin(18), scl=Pin(19), freq=400000)
display = SH1106_I2C(128, 64, i2c, rotate=180)
display.fill(0)  # Clear the display

# first check if wifi credentials are saved
if not connect_to_wifi():
    display_wrapped_text(display, "Starting AP. Connect to PicoSetup, password 12345678")
    captive_portal()
else:
    display_wrapped_text(display, "Connected to WiFi!")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)


    while True:
        if not wlan.isconnected():
            machine.reset()
        
        message = check_messages()
        if message:
            display_wrapped_text(display, message)
        time.sleep(5)

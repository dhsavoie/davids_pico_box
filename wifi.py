import time
import network
from logging import *

def connect_to_wifi(timeout=10):
    try:
        with open("wifi.txt") as f:
            ssid, password = [line.strip() for line in f.readlines()]
        time.sleep(1)
    except:
        print("No WiFi credentials found.")
        log("No wifi credentials found")
        return False
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    print(f"Connecting to {ssid}...")
    wlan.connect(ssid, password)

    start = time.time()
    while time.time() - start < timeout:
        if wlan.isconnected():
            print("Connected! IP Address:", wlan.ifconfig()[0])
            log(f"Connected! IP Address: {wlan.ifconfig()[0]}")
            return wlan
        time.sleep(0.5)

    print("Connection failed. Starting AP...")
    # If it fails, start the setup mode again
    return False

def reconnect_wifi(wlan, timeout=8):
    if wlan.isconnected():
        return True
    
    print("Wifi lost. Attempting reconnection...")
    log("Wifi lost. Attempting reconnection...")
    try:
        with open("wifi.txt") as f:
            ssid, password = [line.strip() for line in f.readlines()]
        time.sleep(1)
    except:
        print("No wifi credentials found.")
        return False
    
    wlan.disconnect()
    time.sleep(1)
    wlan.connect(ssid, password)

    start = time.time()
    while time.time() - start < timeout:
        if wlan.isconnected():
            print("Reconnected! IP Address:", wlan.ifconfig()[0])
            log(f"Reconnected! IP Address: {wlan.ifconfig()[0]}")
            return True
        time.sleep(0.5)
    print("Reconnection failed.")
    return False
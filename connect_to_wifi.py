import machine
import network
import time

def connect_to_wifi():
    try:
        with open("wifi.txt") as f:
            ssid, password = [line.strip() for line in f.readlines()]
        time.sleep(10)
    except:
        print("No WiFi credentials found.")
        return False
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print(f"Connecting to {ssid}...")

    for _ in range(10):
        if wlan.isconnected():
            print("Connected! IP Address:", wlan.ifconfig()[0])
            return True
        time.sleep(1)

    print("Connection failed. Starting AP...")
    # If it fails, start the setup mode again
    return False
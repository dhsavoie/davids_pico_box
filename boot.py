import machine
import network
import time
from lcd import LCD

lcd = LCD(rs=13, e=12, d4=11, d5=10, d6=9, d7=8)

led = machine.Pin("LED", machine.Pin.OUT)

def connect_to_wifi():
    try:
        with open("wifi.txt") as f:
            ssid, password = [line.strip() for line in f.readlines()]
        lcd.clear()
        lcd.write("Connecting...")
        time.sleep(10)
    except:
        print("No WiFi credentials found.")
        return
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print(f"Connecting to {ssid}...")

    for _ in range(10):
        if wlan.isconnected():
            print("Connected! IP Address:", wlan.ifconfig()[0])
            lcd.clear()
            lcd.write("Connected!")
            time.sleep(5)
            led.on()

            import test
        time.sleep(1)

    print("Connection failed. Starting AP...")
    lcd.clear()
    lcd.write("Starting AP...")
    time.sleep(10)
    # If it fails, start the setup mode again
    import main

connect_to_wifi()

import network
import socket
import time
import machine
from my_secrets import pico_AP, pico_AP_pw

def captive_portal():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=pico_AP, password=pico_AP_pw)
    ap.active(True)

    while not ap.active():
        pass

    print("Access Point Active:", ap.ifconfig())

  # HTML Page for Captive Portal
    html = """<!DOCTYPE html>
    <html>
    <head><title>Pico W Setup</title></title></head>
    <body>
        <h2>Enter WiFi Credentials</h2>
        <form action="/" method="POST" enctype="application/x-www-form-urlencoded">
        SSID: <input type="text" name="ssid"><br>
        Password: <input type="text" name="password"><br>
        <input type="submit" value="Connect">
    </form>
    </body>
    </html>
    """  

    addr = ("0.0.0.0", 80)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(addr)
    s.listen(5)

    print("Web server running...")
    while True:
        conn, addr = s.accept()
        print("Client connected from:", addr)
        
        request = conn.recv(1024).decode()
        print("Request Headers:")
        print(request)

        # Capture the content length header and check the body
        content_length = 0
        for line in request.split("\r\n"):
            if "Content-Length" in line:
                content_length = int(line.split(":")[1].strip())

        print(f"Content-Length: {content_length}")

        if content_length > 0:
            # Read the exact number of bytes for the body
            body = conn.recv(content_length).decode()
            print("Request Body:")
            print(body)
        else:
            body = ""

        if "POST" in request:
            print("POST request received...")
            if body:
                # Process the body data
                params = body.split("&")
                ssid, password = params
                ssid = ssid.split("=")[1]
                password = password.split("=")[1]

                print(f"Received SSID: {ssid}, Password: {password}")

                # Save credentials
                with open("wifi.txt", "w") as f:
                    f.write(f"{ssid}\n{password}")

                response = "HTTP/1.1 200 OK\n\n<p>Saved! Restarting...</p>"
                conn.sendall(response.encode())
                conn.close()
                time.sleep(5)
                machine.reset()  # Restart to connect
            else:
                print("Error: No body data received")
                response = "HTTP/1.1 200 OK\n\n<p>Error: No data received. Please try again.</p>"
                conn.sendall(response.encode())
                conn.close()
        else:
            response = "HTTP/1.1 200 OK\nContent-Type: text/html\n\n" + html
            conn.sendall(response.encode())
            conn.close()

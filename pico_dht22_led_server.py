# Pico W DHT22 + LED Web Server (Final Student Version)
# Hardware:
# - DHT22 on GP13
# - LED on GP11 (with 220 ohm resistor)

import network
import socket
import dht
from machine import Pin
import time

# ===== WIFI SETTINGS =====
ssid = 'YOUR_WIFI'
password = 'YOUR_PASSWORD'

# ===== CONNECT TO WIFI =====
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

print("Connecting to WiFi...")
while not wlan.isconnected():
    time.sleep(1)

ip = wlan.ifconfig()[0]
print("Connected! IP:", ip)

# ===== HARDWARE =====
sensor = dht.DHT22(Pin(13))
led = Pin(11, Pin.OUT)

# Start LED OFF
led.value(0)

# ===== WEB PAGE =====
def web_page(temp, hum, led_state):
    led_text = "ON" if led_state else "OFF"
    led_color = "green" if led_state else "red"

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Pico Dashboard</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
</head>
<body style="font-family: Arial; text-align:center;">

    <h1>&#128202; Pico Dashboard</h1>

    <h2>&#127777; Temperature: {temp} &deg;C</h2>
    <h2>&#128167; Humidity: {hum} %</h2>

    <h3 style="color:{led_color};">&#128161; LED is {led_text}</h3>

    <br>

    <a href="/?led=on">
        <button style="padding:15px; font-size:18px;">Turn LED ON</button>
    </a>

    <br><br>

    <a href="/?led=off">
        <button style="padding:15px; font-size:18px;">Turn LED OFF</button>
    </a>

    <p>Auto refresh every 5 seconds</p>

</body>
</html>
"""

# ===== SERVER =====
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)
server.settimeout(2)

print("Web server running at http://", ip)

# ===== MAIN LOOP =====
while True:
    try:
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        try:
            client, addr = server.accept()
        except:
            continue

        request = client.recv(1024).decode()
        print("Request:", request)

        if "GET /?led=on" in request:
            led.value(1)
        elif "GET /?led=off" in request:
            led.value(0)

        response = web_page(temp, hum, led.value())

        client.send("HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8

")
        client.send(response)
        client.close()

    except Exception as e:
        print("Error:", e)
        time.sleep(2)

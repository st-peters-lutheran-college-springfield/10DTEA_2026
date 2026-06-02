# ============================================================
#  Yarning Circle Monitor — Pico W Web Server
#  Hardware:
#    DHT22 sensor  → GP13
#    Red LED       → GP11 (via 220Ω resistor to GND)
# ============================================================
#
#  WIFI MODE — uncomment ONE section below, comment out the other
#
#  ┌─ MODE A: HOTSPOT (recommended — no router needed) ───────
#  │  Pico W creates its own WiFi network
#  │  Connect your device to: YarningMonitor  pw: pico1234
#  │  Then open browser:      http://192.168.4.1
#  └───────────────────────────────────────────────────────────
#
#  ┌─ MODE B: ROUTER (joins existing WiFi) ────────────────────
#  │  Pico W joins your school/home WiFi
#  │  IP address shown in Thonny Shell after connecting
#  │  All devices must be on the same WiFi network
#  └───────────────────────────────────────────────────────────

import network
import socket
import dht
from machine import Pin
import time

# ============================================================
#  WIFI MODE — CHOOSE ONE, COMMENT OUT THE OTHER
# ============================================================

# ── MODE A: HOTSPOT ──────────────────────────────────────────
#  To use: make sure the MODE B block below is commented out

AP_SSID     = 'YarningMonitor'   # WiFi name your device will see
AP_PASSWORD = 'pico1234'         # Must be 8+ characters

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=AP_SSID, password=AP_PASSWORD)
while not ap.active():
    time.sleep(0.5)
ip = ap.ifconfig()[0]            # Always 192.168.4.1
print("Hotspot ready!")
print("Connect to WiFi:", AP_SSID, "  Password:", AP_PASSWORD)
print("Open browser:    http://", ip)

# ── MODE B: ROUTER ───────────────────────────────────────────
#  To use: comment out the MODE A block above, then
#          uncomment every line in this block

# WIFI_SSID     = 'YourNetworkName'   # ← change to your WiFi name
# WIFI_PASSWORD = 'YourPassword'      # ← change to your WiFi password
#
# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect(WIFI_SSID, WIFI_PASSWORD)
# print("Connecting to WiFi...")
# while not wlan.isconnected():
#     time.sleep(1)
# ip = wlan.ifconfig()[0]
# print("Connected! Open browser: http://", ip)

# ============================================================
#  HARDWARE
# ============================================================

sensor = dht.DHT22(Pin(13))
led = Pin(11, Pin.OUT)
led.value(0)   # Start LED off

# ============================================================
#  COMFORT LOGIC
# ============================================================

def comfort_status(temp, hum):
    if temp > 30 or hum > 70:
        return "Too Hot / Humid", "#B03A2E", "⚠️ Not recommended for session"
    elif temp > 26 or hum > 60:
        return "Getting Warm",    "#2B8BE0", "🌡️ Monitor closely"
    else:
        return "Comfortable",     "#2A6B45", "✅ Safe for Yarning Circle"

# ============================================================
#  WEB PAGE
# ============================================================

def web_page(temp, hum, led_state, status_label, status_colour, status_msg):
    led_text = "ON" if led_state else "OFF"
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Yarning Circle Monitor</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="10">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center;
                background: #F5F8FC; padding: 20px; }}
        .status-box {{ background: {status_colour}; color: white;
                       border-radius: 12px; padding: 20px;
                       font-size: 28px; font-weight: bold;
                       margin: 20px auto; max-width: 400px; }}
        .sub-msg {{ font-size: 16px; margin-top: 8px; }}
        .readings {{ font-size: 20px; margin: 16px 0; }}
        button {{ padding: 14px 28px; font-size: 16px; border: none;
                  border-radius: 8px; background: #1A3A5C;
                  color: white; cursor: pointer; }}
    </style>
</head>
<body>
    <h1>Yarning Circle Monitor</h1>

    <div class="status-box">
        {status_label}
        <div class="sub-msg">{status_msg}</div>
    </div>

    <div class="readings">🌡️ Temperature: <strong>{temp} °C</strong></div>
    <div class="readings">💧 Humidity:    <strong>{hum} %</strong></div>

    <p>LED is currently <strong>{led_text}</strong></p>

    <a href="/?led=on" ><button>Turn LED ON</button></a>&nbsp;&nbsp;
    <a href="/?led=off"><button>Turn LED OFF</button></a>

    <p style="color:#888; font-size:13px;">Updates every 10 seconds</p>
</body></html>"""

# ============================================================
#  SERVER
# ============================================================

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)
server.settimeout(2)
print("Web server running at http://", ip)

# ============================================================
#  MAIN LOOP
# ============================================================

while True:
    try:
        # Read sensor first — always before using temp or hum
        sensor.measure()
        temp = sensor.temperature()
        hum  = sensor.humidity()

        label, colour, message = comfort_status(temp, hum)

        try:
            client, addr = server.accept()
        except:
            continue

        request = client.recv(1024).decode()
        print("Request:", request)

        # Update LED state based on button pressed
        if "GET /?led=on" in request:
            led.value(1)
        elif "GET /?led=off" in request:
            led.value(0)

        # Build page AFTER LED update so status reflects the press
        response = web_page(temp, hum, led.value(), label, colour, message)

        client.send("HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html; charset=UTF-8\r\n"
                    "\r\n")
        client.send(response)
        client.close()

    except Exception as e:
        print("Error:", e)
        time.sleep(2)


import time
import os
import json
import board
import digitalio
import busio

import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_wiznet5k.adafruit_wiznet5k as wiznet
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socket

print("\n=== APP START ===")

# ==============================
# 📥 Load config
# ==============================
def safe_get(key, required=True):
    val = os.getenv(key)
    if required and val is None:
        print("Missing:", key)
        while True:
            pass
    return val

DEVICE_ID = safe_get("DEVICE_ID")
BASE_TOPIC = safe_get("BASE_TOPIC")

MQTT_BROKER = safe_get("MQTT_BROKER")
MQTT_PORT = int(safe_get("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

TOPIC = f"{BASE_TOPIC}/{DEVICE_ID}"

# ==============================
# 🌐 Ethernet (reuse)
# ==============================
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.W5500_CS)
rst = digitalio.DigitalInOut(board.W5500_RST)

eth = wiznet.WIZNET5K(spi, cs, rst)
pool = socket.SocketPool(eth)

print("IP:", eth.pretty_ip(eth.ip_address))

# ==============================
# 📡 MQTT
# ==============================
def on_connect(client, userdata, flags, rc):
    print("MQTT connected")

mqtt = MQTT.MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    username=MQTT_USERNAME,
    password=MQTT_PASSWORD,
    client_id=DEVICE_ID,
    socket_pool=pool,
)

mqtt.on_connect = on_connect

while True:
    try:
        mqtt.connect()
        break
    except:
        time.sleep(2)

# ==============================
# 🔌 DIN
# ==============================
pins = [board.GP0, board.GP1, board.GP2, board.GP3]
din = []

for p in pins:
    pin = digitalio.DigitalInOut(p)
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    din.append(pin)

# ==============================
# 🔁 Loop
# ==============================
last = 0

while True:
    mqtt.loop()

    if time.monotonic() - last > 2:
        data = {
            "device": DEVICE_ID,
            "din0": din[0].value,
            "din1": din[1].value,
            "din2": din[2].value,
            "din3": din[3].value,
        }

        payload = json.dumps(data)
        print(payload)

        try:
            mqtt.publish(TOPIC, payload)
        except:
            pass

        last = time.monotonic()

    time.sleep(0.1)

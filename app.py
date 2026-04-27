import time
import os
import json
import digitalio
import board

import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socket
import adafruit_wiznet5k.adafruit_wiznet5k as wiznet

print("\n=== APP SAFE MODE ===")

# reuse existing ethernet (NO reinit risk)
eth = wiznet.WIZNET5K.get_instance()
pool = socket.SocketPool(eth)

DEVICE_ID = os.getenv("DEVICE_ID")
TOPIC = os.getenv("BASE_TOPIC") + "/" + DEVICE_ID

# MQTT (safe reconnect)
mqtt = MQTT.MQTT(
    broker=os.getenv("MQTT_BROKER"),
    port=int(os.getenv("MQTT_PORT")),
    username=os.getenv("MQTT_USERNAME"),
    password=os.getenv("MQTT_PASSWORD"),
    client_id=DEVICE_ID,
    socket_pool=pool,
)

try:
    mqtt.connect()
except:
    pass

# DIN setup
pins = [board.GP0, board.GP1, board.GP2, board.GP3]
din = []

for p in pins:
    d = digitalio.DigitalInOut(p)
    d.direction = digitalio.Direction.INPUT
    d.pull = digitalio.Pull.UP
    din.append(d)

# loop
last = 0

while True:
    try:
        mqtt.loop()
    except:
        try:
            mqtt.connect()
        except:
            pass

    if time.monotonic() - last > 2:

        data = {
            "din0": din[0].value,
            "din1": din[1].value,
            "din2": din[2].value,
            "din3": din[3].value,
        }

        try:
            mqtt.publish(TOPIC, json.dumps(data))
        except:
            pass

        last = time.monotonic()

    time.sleep(0.1)

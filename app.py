import time
import os
import json
import digitalio
import board

import adafruit_minimqtt.adafruit_minimqtt as MQTT

print("\n=== APP SAFE MODE ===")

# ======================
# 🌐 USE EXISTING NETWORK
# ======================
try:
    import global_net
    pool = global_net["pool"]
    eth = global_net["eth"]

    print("Using shared Ethernet:", eth.pretty_ip(eth.ip_address))

except Exception as e:
    print("Network not available:", e)
    while True:
        time.sleep(5)

# ======================
# 📡 MQTT SETUP
# ======================
DEVICE_ID = os.getenv("DEVICE_ID") or "unknown"
BASE_TOPIC = os.getenv("BASE_TOPIC") or "test/device"
TOPIC = BASE_TOPIC + "/" + DEVICE_ID

mqtt = MQTT.MQTT(
    broker=os.getenv("MQTT_BROKER"),
    port=int(os.getenv("MQTT_PORT") or 1883),
    username=os.getenv("MQTT_USERNAME"),
    password=os.getenv("MQTT_PASSWORD"),
    client_id=DEVICE_ID,
    socket_pool=pool,
)

# connect safely
while True:
    try:
        print("Connecting MQTT...")
        mqtt.connect()
        print("MQTT Connected")
        break
    except Exception as e:
        print("MQTT retry:", e)
        time.sleep(2)

# ======================
# 🔌 DIN SETUP
# ======================
pins = [board.GP0, board.GP1, board.GP2, board.GP3]
din = []

for p in pins:
    d = digitalio.DigitalInOut(p)
    d.direction = digitalio.Direction.INPUT
    d.pull = digitalio.Pull.UP
    din.append(d)

# ======================
# 🔁 MAIN LOOP
# ======================
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
        except Exception as e:
            print("Publish error:", e)

        last = time.monotonic()

    time.sleep(0.1)

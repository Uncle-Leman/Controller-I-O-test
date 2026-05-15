import time
import json
import machine
from machine import Pin
from umqtt.simple import MQTTClient

import config


print("\n=== REMOTE APP START ===")


# ======================
# MQTT CONFIG
# ======================
DEVICE_ID = config.DEVICE_ID
BASE_TOPIC = config.BASE_TOPIC
TOPIC = BASE_TOPIC + "/" + DEVICE_ID

MQTT_BROKER = config.MQTT_BROKER
MQTT_PORT = config.MQTT_PORT
MQTT_USERNAME = config.MQTT_USERNAME
MQTT_PASSWORD = config.MQTT_PASSWORD


# ======================
# AUTO REBOOT CONFIG
# ======================
REBOOT_INTERVAL_MS = 10 * 60 * 1000   # 10 minutes
boot_time = time.ticks_ms()


# ======================
# MQTT CONNECT
# ======================
def connect_mqtt():
    client = MQTTClient(
        client_id=DEVICE_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USERNAME,
        password=MQTT_PASSWORD,
        keepalive=60
    )

    while True:
        try:
            print("Connecting MQTT...")
            client.connect()
            print("MQTT connected")
            return client
        except Exception as e:
            print("MQTT retry:", e)
            time.sleep(2)


# ======================
# SAFE SOFT REBOOT
# ======================
def reboot_controller(reason="Scheduled reboot"):
    print("\n======================")
    print(reason)
    print("Controller will reboot now...")
    print("======================")

    try:
        mqtt.publish(
            TOPIC + "/status",
            json.dumps({
                "device": DEVICE_ID,
                "status": "rebooting",
                "reason": reason
            })
        )
    except Exception as e:
        print("Failed to publish reboot status:", e)

    try:
        mqtt.disconnect()
    except:
        pass

    time.sleep(1)

    try:
        machine.soft_reset()
    except AttributeError:
        machine.reset()


mqtt = connect_mqtt()


# ======================
# DIN
# ======================
pins = [
    Pin(0, Pin.IN, Pin.PULL_UP),
    Pin(1, Pin.IN, Pin.PULL_UP),
    Pin(2, Pin.IN, Pin.PULL_UP),
    Pin(3, Pin.IN, Pin.PULL_UP),
]


# ======================
# MAIN LOOP
# ======================
last_publish = 0

while True:
    now = time.ticks_ms()

    # Auto reboot every 10 minutes
    if time.ticks_diff(now, boot_time) >= REBOOT_INTERVAL_MS:
        reboot_controller("Auto reboot after 10 minutes")

    # Publish DIN every 2 seconds
    if time.ticks_diff(now, last_publish) > 2000:
        data = {
            "din0": bool(pins[0].value()),
            "din1": bool(pins[1].value()),
            "din2": bool(pins[2].value()),
            "din3": bool(pins[3].value()),
        }

        payload = json.dumps(data)
        print(payload)

        try:
            mqtt.publish(TOPIC, payload)
        except Exception as e:
            print("Publish error:", e)

            try:
                mqtt.disconnect()
            except:
                pass

            mqtt = connect_mqtt()

        last_publish = now

    time.sleep(0.1)

import time
import gc
import machine
import json

from umqtt.simple import MQTTClient

import config


mqtt = None
mqtt_fail_count = 0


def cleanup_mqtt():
    global mqtt

    print("Cleaning MQTT...")

    if mqtt is not None:
        try:
            mqtt.disconnect()
        except Exception:
            pass

        try:
            mqtt.sock.close()
        except Exception:
            pass

    mqtt = None
    gc.collect()


def connect_mqtt():
    global mqtt, mqtt_fail_count

    cleanup_mqtt()

    print("Connecting MQTT...")

    try:
        mqtt = MQTTClient(
            client_id=config.MQTT_CLIENT_ID,
            server=config.MQTT_BROKER,
            port=config.MQTT_PORT,
            keepalive=30
        )

        mqtt.connect()
        mqtt_fail_count = 0
        print("MQTT connected")
        return True

    except Exception as e:
        mqtt_fail_count += 1
        print("MQTT retry:", e)
        cleanup_mqtt()
        time.sleep(5)
        return False


def publish_safe(topic, payload):
    global mqtt, mqtt_fail_count

    if mqtt is None:
        if not connect_mqtt():
            return False

    try:
        mqtt.publish(topic, payload)
        print(payload)
        mqtt_fail_count = 0
        return True

    except Exception as e:
        mqtt_fail_count += 1
        print("Publish error:", e)

        cleanup_mqtt()

        if mqtt_fail_count >= 10:
            print("Too many MQTT failures. Rebooting...")
            time.sleep(2)
            machine.reset()

        return False

import time
import os
import json
import board
import digitalio
import busio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_wiznet5k.adafruit_wiznet5k as wiznet
import adafruit_wiznet5k.adafruit_wiznet5k_socketpool as socket

# --- MQTT Settings ---
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_PUB_TOPIC = os.getenv("MQTT_PUB_TOPIC")

# --- Ethernet Setup ---
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.W5500_CS)
rst = digitalio.DigitalInOut(board.W5500_RST)

eth = wiznet.WIZNET5K(spi, cs, rst)
pool = socket.SocketPool(eth)

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT")

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT")

# --- MQTT Client ---
mqtt = MQTT.MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    username=MQTT_USERNAME,
    password=MQTT_PASSWORD,
    client_id=MQTT_CLIENT_ID,
    socket_pool=pool,
    is_ssl=False,
)

mqtt.on_connect = on_connect
mqtt.on_disconnect = on_disconnect

mqtt.connect()

# --- Digital Inputs Setup ---
pins = [board.GP0, board.GP1, board.GP2, board.GP3]
din = []

for p in pins:
    pin = digitalio.DigitalInOut(p)
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.UP
    din.append(pin)

# --- Helper: Current Time ---
def curr_time():
    t = time.localtime()
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"

# --- Main Loop ---
last_pub = 0
INTERVAL = 2  # seconds

mqtt_connected = False
last_pub = 0

while True:
    # --- MQTT loop ---
    try:
        mqtt.loop()
        mqtt_connected = True
    except Exception as e:
        print("MQTT loop error:", e)
        mqtt_connected = False

    # --- Reconnect if needed ---
    if not mqtt_connected:
        try:
            print("Trying reconnect...")
            mqtt.connect()
            mqtt_connected = True
        except:
            time.sleep(2)
            continue

    # --- Normal operation ---
    if time.monotonic() - last_pub > 2:
        data = {
            "din0": din[0].value,
            "din1": din[1].value,
            "din2": din[2].value,
            "din3": din[3].value,
        }

        payload = json.dumps(data)
        print("Publishing:", payload)

        try:
            mqtt.publish(MQTT_PUB_TOPIC, payload)
        except Exception as e:
            print("Publish failed:", e)
            mqtt_connected = False

        last_pub = time.monotonic()

    time.sleep(0.1)

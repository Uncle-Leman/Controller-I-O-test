# app.py
# This file is downloaded from GitHub.

import time
import net

print("\n=== APP STARTED ===")

nic = net.connect()

print("Running main application...")
print("IP:", nic.ifconfig()[0])

while True:
    print("DIN0: true | DIN1: false")
    time.sleep(5)

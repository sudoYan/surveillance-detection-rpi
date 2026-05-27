import os
import sys
import time
import argparse
import threading
import subprocess
import json
import csv
from datetime import datetime

# Optional GPIO support - not ready yet
#try:
    #import RPi.GPIO as GPIO
    #GPIO_AVAILABLE = True
#except ImportError:
    #GPIO_AVAILABLE = False

# Scapy for WiFi promiscuous sniffing
try:
    from scapy.all import sniff, Dot11, Dot11ProbeReq, Dot11Elt
except ImportError:
    print("[-] Error: Scapy is required. Run 'pip install scapy'")
    sys.exit(1)

# Bleak for asynchronous Bluetooth LE scanning
try:
    import asyncio
    from bleak import BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

# Serial for GPS reading
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# GLOBAL STATE & THREAD SAFETIES
state = {
    "gps_coords": {"lat": 0.0, "lon": 0.0, "alt": 0.0, "time": "00:00:00", "valid": False},
    "detections": {},  # MAC -> Detection Details
    "scan_active": True,
    "current_channel": 1,
    "interface": "wlan0mon",
    "buzzer_pin": 21,
    "led_pin": 20,
    "alert_queue": [],
    "total_hits": 0,
    "session_id": datetime.now().strftime("%Y%m%d_%H%M%S")
}

state_lock = threading.Lock()
csv_file = f"flock_detections_{state['session_id']}.csv"


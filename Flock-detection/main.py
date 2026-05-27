import os
import sys
import time
import argparse
import threading
import subprocess
import json
import csv
from datetime import datetime
from wifi_sniffer import channel_hopper_thread, wifi_packet_callback
from gps_receiver import gps_reader_thread
from ble_detection import run_async_ble
from ui_detector import print_dashboard

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

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[-] Error: This counter-surveillance tool requires raw socket operations.")
        print("[-] Please execute with root privileges: 'sudo python3 flock_you_pi.py'")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Flock-You Pi: Hardware Passive Surveillance Sniffer")
    parser.add_argument("-i", "--interface", required=True, help="Wireless Sniffing interface (must support monitor mode, e.g. wlan1mon)")
    parser.add_argument("-g", "--gps", default=None, help="GPS device file path (e.g., /dev/ttyUSB0)")
    parser.add_argument("-b", "--buzzer", type=int, default=21, help="Broadcom BCM GPIO pin for piezo buzzer (default 21)")
    parser.add_argument("-l", "--led", type=int, default=20, help="Broadcom BCM GPIO pin for tracking indicator LED (default 20)")
    args = parser.parse_args()

    state["interface"] = args.interface
    state["buzzer_pin"] = args.buzzer
    state["led_pin"] = args.led

    # Init physical boards
    #setup_gpio()

    # 1. Start Channel Hopper Thread
    hopper = threading.Thread(target=channel_hopper_thread, args=(state["interface"],), daemon=True)
    hopper.start()

    # 2. Start GPS Thread (if passed)
    if args.gps:
        gps_t = threading.Thread(target=gps_reader_thread, args=(args.gps,), daemon=True)
        gps_t.start()

    # 3. Start BLE Scanner Thread
    if BLE_AVAILABLE:
        ble_t = threading.Thread(target=run_async_ble, daemon=True)
        ble_t.start()

    # 4. Start Dashboard TUI Update Thread
    dash_t = threading.Thread(target=print_dashboard, daemon=True)
    dash_t.start()

    # 5. Execute Core WiFi Sniffer Loop
    print(f"[*] Sniffing active on interface {state['interface']}...")
    try:
        sniff(iface=state["interface"], prn=wifi_packet_callback, store=0)
    except KeyboardInterrupt:
        print("\n[*] Shutting down tracking systems. Session ended.")
    finally:
        state["scan_active"] = False
        #if GPIO_AVAILABLE:
            #GPIO.cleanup()
        print("[*] Resources cleaned. Stay safe out there!")
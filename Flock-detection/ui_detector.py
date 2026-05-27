import os
import sys
import time
import argparse
import threading
import subprocess
import json
import csv
from datetime import datetime

#Terminal User Interface Drawing
def print_alert_box(csv_file, mac, type_, method, rssi, lat, lon):
    """Draws an eye-catching warning box to the system shell upon discovery."""
    border = "======================================================================"
    print(f"\n\033[91m{border}")
    print(f" ⚠️  SURVEILLANCE CAMERA/INFRASTRUCTURE IDENTIFIED nearby!")
    print(f"{border}\033[0m")
    print(f" 📡 MAC Address  : \033[1m{mac.upper()}\033[0m (OUI: {mac[:8]})")
    print(f" 🏷️  Device Class : \033[93m{type_}\033[0m")
    print(f" 🔬 Sniff Signature: {method}")
    print(f" 📶 Signal Strength: {rssi} dBm")
    print(f" 🗺️  GPS Location  : {lat}, {lon}")
    print(f" 💾 Auto-Logged to : \033[32m{csv_file}\033[0m")
    print(f"\033[91m{border}\033[0m\n")

def print_dashboard(state, state_lock, BLE_AVAILABLE):
    """Outputs real-time background parameters and coordinates to the screen."""
    while state["scan_active"]:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("="*70)
        print(f" FLOCK-YOU : PASSIVE RASPBERRY PI SURVEILLANCE RADAR (Session: {state['session_id']})")
        print("="*70)
        print(f" WiFi Sniffer Interface : \033[96m{state['interface']}\033[0m [CH: {state['current_channel']}]")
        print(f" BLE Radio Scanner      : {'Enabled (Bleak)' if BLE_AVAILABLE else 'Disabled'}")
        
        gps_status = "\033[92m3D FIX ESTABLISHED\033[0m" if state["gps_coords"]["valid"] else "\033[91mSEARCHING FOR SATELLITES...\033[0m"
        print(f" GPS Spatial Engine     : {gps_status}")
        print(f" Active Target Location : {state['gps_coords']['lat']}, {state['gps_coords']['lon']}")
        print(f" Active Targets Logged  : \033[91m\033[1m{state['total_hits']}\033[0m unique nodes")
        print("="*70)
        print(" Recent Unique Tracked Detections:")
        print(f" {'TIMESTAMP':<19} | {'MAC ADDRESS':<17} | {'RSSI':<5} | {'TYPE':<25}")
        print("-"*70)
        
        with state_lock:
            # Display last 8 active targets
            recent_hits = sorted(state["detections"].items(), key=lambda x: x[1]['last_seen'], reverse=True)[:8]
            for mac, info in recent_hits:
                print(f" {info['last_seen']} | {mac.upper()} | {str(info['rssi']):<5} | {info['type'][:25]}")
        
        print("\nPress [Ctrl+C] safely to power down tracking.")
        time.sleep(2.0)
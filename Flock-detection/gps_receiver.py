import os
import sys
import time
import argparse
import threading
import subprocess
import json
import csv
from datetime import datetime
import serial

# GPS RECEIVER ENGINE (NMEA Parsing)
def gps_reader_thread(SERIAL_AVAILABLE, state, state_lock, port, baudrate=9600):
    if not SERIAL_AVAILABLE:
        print("[-] PySerial not installed. GPS logging disabled.")
        return

    print(f"[*] Starting GPS polling on {port} ({baudrate} bps)...")
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        while state["scan_active"]:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line.startswith('$GPRMC') or line.startswith('$GNRMC'):
                parts = line.split(',')
                if len(parts) > 6 and parts[2] == 'A':  # 'A' means data valid
                    try:
                        # Parse Latitude
                        raw_lat = float(parts[3])
                        lat_deg = int(raw_lat / 100)
                        lat_min = raw_lat - (lat_deg * 100)
                        lat = lat_deg + (lat_min / 60.0)
                        if parts[4] == 'S':
                            lat = -lat

                        # Parse Longitude
                        raw_lon = float(parts[5])
                        lon_deg = int(raw_lon / 100)
                        lon_min = raw_lon - (lon_deg * 100)
                        lon = lon_deg + (lon_min / 60.0)
                        if parts[6] == 'W':
                            lon = -lon

                        with state_lock:
                            state["gps_coords"]["lat"] = round(lat, 6)
                            state["gps_coords"]["lon"] = round(lon, 6)
                            state["gps_coords"]["time"] = parts[1][:6]
                            state["gps_coords"]["valid"] = True
                    except ValueError:
                        pass
            time.sleep(0.1)
    except Exception as e:
        print(f"[-] GPS Thread failed to bind or read: {e}. Running without GPS spatial correlation.")

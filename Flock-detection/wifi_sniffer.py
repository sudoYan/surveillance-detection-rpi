import os
import sys
import time
import argparse
import threading
import subprocess
import json
import csv
from datetime import datetime
from gpio_funcs import trigger_alert
from ui_detector import print_alert_box
from oui import FLOCK_OUIS

try:
    from scapy.all import sniff, Dot11, Dot11ProbeReq, Dot11Elt
except ImportError:
    print("[-] Error: Scapy is required. Run 'pip install scapy'")
    sys.exit(1)

# AUTOMATED CHANNEL HOPPING (WiFi Sniffer optimization)
def channel_hopper_thread(state, interface):
    """Hops across critical 2.4GHz channels (1, 6, 11) to locate active cameras."""
    channels = [1, 6, 11]
    idx = 0
    print(f"[*] Initialized Channel Hopper thread on interface: {interface}")
    while state["scan_active"]:
        state["current_channel"] = channels[idx]
        try:
            subprocess.run(["iw", "dev", interface, "set", "channel", str(state["current_channel"])],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            try:
                subprocess.run(["iwconfig", interface, "channel", str(state["current_channel"])],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"[-] Channel hop error: {e}. Ensure you run as sudo.")
                break
        idx = (idx + 1) % len(channels)
        time.sleep(0.350)  # 350ms dwell time per channel

# PROCESS DETECTIONS (Unified Core Logic)
def record_detection(mac, state, state_lock, csv_file, device_type, method, rssi, extra_info=""):
    """Validates, records, logs, and triggers audio-visual feedback."""
    mac = mac.lower()
    oui = mac[:8]

    # Block Randomized/Locally-Administered MACs from triggering false positives
    # (Byte 0, bit 1 set to 1 indicates a randomized/private MAC address)
    try:
        first_byte = int(mac.split(':')[0], 16)
        if first_byte & 2:
            return  # Filtered: Randomized Client Address
    except ValueError:
        pass

    with state_lock:
        is_new = mac not in state["detections"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Pull spatial frame
        lat = state["gps_coords"]["lat"] if state["gps_coords"]["valid"] else "N/A"
        lon = state["gps_coords"]["lon"] if state["gps_coords"]["valid"] else "N/A"

        state["detections"][mac] = {
            "last_seen": now,
            "type": device_type,
            "method": method,
            "rssi": rssi,
            "lat": lat,
            "lon": lon,
            "info": extra_info
        }

        if is_new:
            state["total_hits"] += 1
            # Append atomic save row
            try:
                file_exists = os.path.exists(csv_file)
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Timestamp", "MAC", "OUI", "Device Type", "Method", "RSSI", "Latitude", "Longitude", "Extra"])
                    writer.writerow([now, mac, oui, device_type, method, rssi, lat, lon, extra_info])
            except IOError as e:
                print(f"[-] Database Write Error: {e}")

            # Draw alert card to console
            print_alert_box(mac, device_type, method, rssi, lat, lon)
            trigger_alert()

def wifi_packet_callback(pkt, state):
    """Callback triggered on every 802.11 frame captured in promiscuous mode."""
    if not pkt.haslayer(Dot11):
        return

    # Check Transmitter (addr2), Receiver (addr1), and BSSID (addr3)
    addr1 = pkt.addr1
    addr2 = pkt.addr2
    addr3 = pkt.addr3
    rssi = 0

    # Retrieve RSSI if available in Radiotap header
    if pkt.haslayer('RadioTap'):
        try:
            rssi = pkt.dBm_AntSignal
        except AttributeError:
            pass

    # Signature 1: High Precision Wildcard Probe Request (DeFlockJoplin Spec)
    if pkt.haslayer(Dot11ProbeReq):
        # Scan for SSID Element
        el = pkt.getlayer(Dot11Elt)
        is_wildcard = False
        while el:
            if el.ID == 0 and el.len == 0:  # SSID tag with length 0
                is_wildcard = True
                break
            el = el.payload.getlayer(Dot11Elt)

        if is_wildcard and addr2:
            oui = addr2[:8].lower()
            if oui in FLOCK_OUIS:
                record_detection(
                    mac=addr2,
                    device_type="Flock ALPR (Solar/Battery)",
                    method="wifi_wildcard_probe",
                    rssi=rssi,
                    extra_info="Wildcard SSID probe request"
                )
                return

    # Signature 2: Transmitter OUI Match
    if addr2:
        oui = addr2[:8].lower()
        if oui in FLOCK_OUIS:
            record_detection(
                mac=addr2,
                device_type="Flock Device",
                method="wifi_oui_addr2",
                rssi=rssi,
                extra_info=f"Active Tx Frame (CH: {state['current_channel']})"
            )
            return

    # Signature 3: Receiver OUI Match (Target of active frames nearby)
    if addr1 and addr1 != "ff:ff:ff:ff:ff:ff":
        oui = addr1[:8].lower()
        if oui in FLOCK_OUIS:
            record_detection(
                mac=addr1,
                device_type="Flock Infrastructure Target",
                method="wifi_oui_addr1",
                rssi=rssi,
                extra_info="Passive Node Frame Target"
            )
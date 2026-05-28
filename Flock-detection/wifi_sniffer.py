import os
import sys
import time
import argparse
import threading
import subprocess
import json
from datetime import datetime
from oui import FLOCK_OUIS
from recording_mechanism import record_detection

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

def wifi_packet_callback(pkt, state, state_lock, csv_file):
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
                    state= state,
                    state_lock= state_lock,
                    csv_file= csv_file,
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
                state= state,
                state_lock= state_lock,
                csv_file= csv_file,
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
                state= state,
                state_lock= state_lock,
                csv_file= csv_file,
                device_type="Flock Infrastructure Target",
                method="wifi_oui_addr1",
                rssi=rssi,
                extra_info="Passive Node Frame Target"
            )
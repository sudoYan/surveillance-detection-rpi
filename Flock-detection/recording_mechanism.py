# PROCESS DETECTIONS (Unified Core Logic)
#from gpio_funcs import trigger_alert
from ui_detector import print_alert_box
from datetime import datetime
import os
import csv

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
            print_alert_box(csv_file, mac, device_type, method, rssi, lat, lon)
            #trigger_alert(state, GPIO_AVAILABLE)
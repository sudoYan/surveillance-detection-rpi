from oui import FLOCK_OUIS, BLE_COMPANY_IDS, BLE_NAME_KEYWORDS
from recording_mechanism import record_detection
try:
    import asyncio
    from bleak import BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

#Asynchronous BLE detection and scanning loop
async def ble_scanner_loop(state, state_lock, csv_file):
    """Asynchronous background loop scanning for diagnostic BLE indicators."""
    if not BLE_AVAILABLE:
        return

    print("[*] Launching Passive BLE scanner...")
    while state["scan_active"]:
        try:
            # Short passive discovery scan (3 seconds window)
            devices = await BleakScanner.discover(timeout=3.0, return_adv=True)
            for d, adv in devices.values():
                mac = d.address.lower()
                name = adv.local_name or ""
                m_data = adv.manufacturer_data
                rssi = adv.rssi

                # Fingerprint match 1: Target OUI check
                if mac[:8] in FLOCK_OUIS:
                    record_detection(mac, state, state_lock, csv_file, "Flock Controller (BLE)", "ble_oui", rssi, f"Name: {name}")
                    continue

                # Fingerprint match 2: Company ID check
                matched_id = any(cid in BLE_COMPANY_IDS for cid in m_data.keys()) if m_data else False
                if matched_id:
                    record_detection(mac, "Flock External Battery Unit", "ble_manufacturer_id", rssi, "OUI-SPY Compatible Battery Node")
                    continue

                # Fingerprint match 3: Name signature scan
                if any(kw in name.upper() for kw in BLE_NAME_KEYWORDS):
                    record_detection(mac, "ALPR Field Module", "ble_name_match", rssi, f"Broadcast: {name}")

        except Exception as e:
            # Suppress temporary bus locks and hot loops
            await asyncio.sleep(2)
        await asyncio.sleep(1.5)

def run_async_ble(state, state_lock, csv_file):
    if BLE_AVAILABLE:
        asyncio.run(ble_scanner_loop(state, state_lock, csv_file))

"""async def ble_scanner_loop(state, state_lock, csv_file):
    
    #DEBUG MODE: Scans and prints ANY visible BLE device to verify hardware and library functionality on your laptop.
    
    if not BLE_AVAILABLE:
        print("[-] BLE is not available in this environment.")
        return

    print("\n\033[94m[*] LAUNCHING PASSIVE BLE DEBUG SCANNER...")
    print("[*] Bypassing all filters. Printing ALL nearby BLE broadcasts...\033[0m\n")
    
    while state["scan_active"]:
        try:
            # 3-second discovery window
            devices = await BleakScanner.discover(timeout=3.0, return_adv=True)
            
            if not devices:
                print("[*] Scan window finished: 0 BLE devices seen in the last 3 seconds.")
            
            for d, adv in devices.values():
                mac = d.address.lower()
                name = adv.local_name or "Unknown Name"
                m_data = list(adv.manufacturer_data.keys()) if adv.manufacturer_data else "None"
                rssi = adv.rssi

                # 1. Immediate Verbose Terminal Print for Testing
                print(f"📡 [FOUND] MAC: {mac.upper()} | RSSI: {rssi}dBm | Name: {name} | Company IDs: {m_data}")

                # 2. Check if it happens to match your Flock OUI target array anyway
                if mac[:8] in FLOCK_OUIS:
                    print(f"    \033[92m🎯 MATCHED TARGET OUI: {mac[:8]} (Sending to database)\033[0m")
                    record_detection(mac, state, state_lock, csv_file, "Flock Controller (BLE)", "ble_oui", rssi, f"Name: {name}")
                    continue

                # 3. Check Name keyword matches anyway (Fixed arguments here)
                if any(kw in name.upper() for kw in BLE_NAME_KEYWORDS):
                    print(f"    \033[92m🎯 MATCHED TARGET KEYWORD: {name} (Sending to database)\033[0m")
                    record_detection(mac, state, state_lock, csv_file, "ALPR Field Module", "ble_name_match", rssi, f"Broadcast: {name}")
                    continue

                # 4. Check Company ID matches anyway (Fixed arguments here)
                matched_id = any(cid in BLE_COMPANY_IDS for cid in adv.manufacturer_data.keys()) if adv.manufacturer_data else False
                if matched_id:
                    print(f"    \033[92m🎯 MATCHED BATTERY MODULE ID (Sending to database)\033[0m")
                    record_detection(mac, state, state_lock, csv_file, "Flock External Battery Unit", "ble_manufacturer_id", rssi, "OUI-SPY Compatible Battery Node")
                    continue

        except Exception as e:
            print(f"[\033[91m!\033[0m] BLE Debug Loop Error: {e}")
            await asyncio.sleep(2)
            
        # Short breather between scan windows
        await asyncio.sleep(1.5)

def run_async_ble(state, state_lock, csv_file):
    if BLE_AVAILABLE:
        asyncio.run(ble_scanner_loop(state, state_lock, csv_file))"""
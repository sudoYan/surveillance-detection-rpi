from oui import FLOCK_OUIS, BLE_COMPANY_IDS, BLE_NAME_KEYWORDS
from recording_mechanism import record_detection
try:
    import asyncio
    from bleak import BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

#Asynchronous BLE detection and scanning loop
async def ble_scanner_loop(state):
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
                    record_detection(mac, "Flock Controller (BLE)", "ble_oui", rssi, f"Name: {name}")
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

def run_async_ble():
    if BLE_AVAILABLE:
        asyncio.run(ble_scanner_loop())
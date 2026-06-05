# Known Organizationally Unique Identifiers (OUIs) used by Flock Safety modules.
# Includes primary Espressif (ESP32-S3/WROOM) modules and confirmed hardware suppliers.
FLOCK_OUIS = {
    # Primary Espressif (ESP32 / System-on-Chip modules)
    "d4:ad:fc", "ac:67:b2", "84:f3:eb", "b4:e6:2d", "cc:db:a7", 
    "24:0a:c4", "30:ae:a4", "94:b9:7e", "a4:cf:12", "c0:49:ef",
    # Known Falcon/Raven Camera suppliers & vendor-registered OUIs
    "70:c9:4e", "3c:91:80", "d8:f3:bc", "80:30:49", "b8:35:32", 
    "14:5a:fc", "74:4c:a1", "08:3a:88", "9c:2f:9d", "c0:35:32", 
    "94:08:53", "e4:aa:ea", "f4:6a:dd", "f8:a2:d6", "24:b2:b9", 
    "00:f4:8d", "d0:39:57", "e8:d0:fc", "e0:4f:43", "b8:1e:a4", 
    "70:08:94", "58:8e:81", "ec:1b:bd", "3c:71:bf", "58:00:e3", 
    "90:35:ea", "5c:93:a2", "64:6e:69", "48:27:ea", "b4:1e:52",
    # Special Community-discovered OUI signatures
    "82:6b:f2", "e0:0a:f6"
    #DEBUG
    "f8:bc:12", "00:0c:8a", "04:52:c7", "08:df:1f", "28:11:a5",
    "2c:41:a1", "4c:87:5d", "60:ab:d2", "68:f2:1f", "78:2b:64",
    "ac:bf:71", "bc:87:fa", "c8:7b:23", "e4:58:bc"
}

# BLE Specific fingerprints (Axon/Flock/Raven beacons)
BLE_COMPANY_IDS = {0x09C8}  # XUNTONG battery monitor / diagnostics
BLE_NAME_KEYWORDS = ["FLOCK", "RAVEN", "AXON", "SOLAR", "LPR"]
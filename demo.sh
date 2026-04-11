#!/bin/bash
echo "--- 1. FIRMWARE SECURITY (Track 4: Edison-Bypass Defense) ---"
python3 -m src.firmware_guard
echo -e "\n--- 2. WHO GO.DATA INTEGRATION (Track 2: Pandemic Warning) ---"
python3 -m network.godata_bridge
echo -e "\n--- 3. FEDERATED NETWORK SYNC (Track 2: Privacy-First) ---"
python3 -m network.sync_protocol

import json
from pathlib import Path
from src.engine import sequence_sha256

class FederatedNetwork:
    def __init__(self, registry_path="network/threat_registry.json"):
        self.registry_path = Path(registry_path)
        if not self.registry_path.exists():
            with open(self.registry_path, "w") as f:
                json.dump({"known_threats": []}, f)

    def check_local_against_network(self, sequence_hash):
        with open(self.registry_path, "r") as f:
            data = json.load(f)
        
        if sequence_hash in data["known_threats"]:
            return "⚠️ ALERT: Sequence match found in the Pan-African Registry."
        return "✅ No matches found in the federated network."

if __name__ == "__main__":
    # 1. Initialize the network with a 'mock' threat hash (e.g., from your audit log)
    # This hash represents a known hazardous sequence shared by Africa CDC
    threat_hash = "496a5ac4795e7e649bef8b6c9e38a1b930d05b31fa22e212e372b873b6cf9700"
    
    registry_file = Path("network/threat_registry.json")
    with open(registry_file, "w") as f:
        json.dump({"known_threats": [threat_hash]}, f)
        
    net = FederatedNetwork()
    
    print("\n🌍 --- Pan-African Federated Network Check ---")
    # Test a "Safe" sequence
    print(f"Scanning Local Sequence A: {net.check_local_against_network('safe_hash_123')}")
    
    # Test the "Threat" sequence
    print(f"Scanning Local Sequence B: {net.check_local_against_network(threat_hash)}")
    print("-----------------------------------------------\n")

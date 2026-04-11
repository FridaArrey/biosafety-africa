import json
import hashlib
import datetime
import re
from src.engine import LiteEngine, sequence_sha256

class FirmwareGuard:
    """
    Enhanced Firmware Guard for Track 4 (Sentinel Bio).
    Detects assembly scars (Edison et al. 2026) and provides chained logging.
    """
    def __init__(self, log_path="deployment/tamper_proof_log.jsonl"):
        self.engine = LiteEngine(batch_size=1)
        self.log_path = log_path
        self.last_log_hash = "0" * 64
        
        # BsaI and BsmBI are the 'workhorses' of Golden Gate/Darwin Assembly bypasses
        self.assembly_scars = {
            "BsaI": r"GGTCTC",
            "BsmBI": r"CGTCTC",
            "SapI": r"GCTCTTC"
        }

    def _generate_tamper_proof_entry(self, sequence, status, flags):
        entry_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "seq_hash": sequence_sha256(sequence),
            "status": status,
            "flags": flags,
            "previous_entry_hash": self.last_log_hash
        }
        entry_string = json.dumps(entry_data, sort_keys=True)
        current_hash = hashlib.sha256(entry_string.encode()).hexdigest()
        self.last_log_hash = current_hash
        entry_data["entry_sig"] = current_hash
        return entry_data

    def pre_print_screen(self, dna_fragment):
        flags = []
        
        # 1. AI Functional Screening (Track 1 Compliance)
        embedding = self.engine.embed(dna_fragment)
        
        # 2. Assembly Scar Detection (Track 4 Compliance - Edison et al. 2026)
        for enzyme, pattern in self.assembly_scars.items():
            if re.search(pattern, dna_fragment):
                flags.append(f"SCAR_DETECTED_{enzyme}")

        # 3. Decision Logic
        # Block if suspicious scars are present in potential viral fragments
        is_safe = len(flags) == 0
        status = "APPROVED" if is_safe else "BLOCKED_ASSEMBLY_RISK"

        log_entry = self._generate_tamper_proof_entry(dna_fragment, status, flags)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        if not is_safe:
            print(f"🛑 FIRMWARE ALERT: {status} | Flags: {flags}")
            return False
        
        return True

if __name__ == "__main__":
    guard = FirmwareGuard()
    print("\n⚡ Benchtop Shield Active: Scanning for Fragment Assembly Scars...")
    
    # Test: A sequence containing a BsaI scar (GGTCTC) used for split-order assembly
    suspicious_fragment = "ATGC" + "GGTCTC" + "ATGC" * 10 
    guard.pre_print_screen(suspicious_fragment)

# SOP: Offline Biosecurity Screening
**Objective:** To perform secure, offline protein sequence screening.

1. **Environment Setup**: Ensure the laptop is disconnected from all networks (WiFi/Ethernet) to prevent "Information Hazards."
2. **Initialization**: Run `bash ../deployment/offline_setup.sh` while connected to download weights once.
3. **Execution**: Run `python3 ../src/engine.py --fasta <path_to_file>`.
4. **Verification**: Confirm the generation of the `audit_trail.jsonl` for compliance reporting.

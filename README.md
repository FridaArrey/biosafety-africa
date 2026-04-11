# BioSafety Africa 🌍🛡️
**AI-Enhanced Synthesis Screening for Resource-Constrained African Biosafety Laboratories**

## Mission
Democratizing biosecurity through accessible, cost-effective AI threat detection.

## Quick Start for Lab Technicians

1. **Air-gap the model (one-time, with network)**  
   From the repository root, download ESM-2 8M, tokenizer, manifest, and starter HMM profiles for offline use:
   ```bash
   bash deployment/offline_setup.sh
   ```
   After this, `src/engine.py` can load weights from `models/esm2_8m` without calling the public internet (see `docs/compliance_benchmarks.md` for related compliance inputs).

2. **Scan sequences on the lab CPU**  
   Run embeddings locally (no GPU required). From the **repository root**:
   ```bash
   python3 src/engine.py --sequence MKTAYIAKQRQISFVKSHFSRQ
   ```
   Or embed every record in a FASTA file:
   ```bash
   python3 src/engine.py --fasta path/to/sequences.faa
   ```
   Output includes embedding dimension, a **SHA-256 hash** of the sequence (for audit trails), and optionally batch shape for multi-record files.

3. **Compliance & sustainability report for administrators**  
   Generate a cost and CO₂e comparison (cloud API vs local laptop-class CPU) using the **2026** figures in `docs/compliance_benchmarks.md`:
   ```bash
   python3 tools/cost_calc.py -n 5000 --region Kenya
   ```
   Replace `5000` with your batch count and set `--region` to the site’s country. Share the printed table and summary with hospital or institutional administrators.

### 2026 audited planning comparison (example run)

Figures below come from **`python3 tools/cost_calc.py -n 5000`** with **engine reference timing** (0.42 s/sequence), **30 W** laptop draw, and compliance defaults for API fee, bandwidth, and implied cloud kWh/sequence. *Dollar savings vs the modeled cloud API are the same in both rows; local grid intensity drives the difference in on-site CO₂e.*

| Country | Sequences (modeled) | Savings vs cloud API (USD) | Local CO₂e (kg) | Net CO₂e vs cloud API (kg) |
|--------|---------------------|------------------------------|-----------------|----------------------------|
| Kenya | 5,000 | $49.997 | 0.0025 | 5.77 |
| Nigeria | 5,000 | $49.997 | 0.0084 | 5.77 |

*Net CO₂e = modeled cloud column minus local column (positive ⇒ lower footprint when processing locally). At two decimal places both nets round to **5.77 kg**; Nigeria’s higher grid factor shows up in the larger **local** CO₂e (0.0084 vs 0.0025 kg). Re-run `cost_calc` for your own volume, region, and optional `--benchmark` timing.*

## Sustainability — African Lab Advantage

Screening with a **local CPU** (offline-capable ESM-2 8M in `src/engine.py`) avoids shipping sequences to **US-hosted GPU APIs**, which concentrates energy use in high–power-density data centers and adds long-haul network transfers.

- **Carbon:** For the same workload model, emissions scale with **kWh × grid kg CO2e/kWh**. African sites use **2026 audited planning factors** in [docs/compliance_benchmarks.md](docs/compliance_benchmarks.md) (e.g. Kenya **0.14**, Nigeria **0.48**, South Africa **0.89** kg CO2e/kWh). The cloud column uses an illustrative US-style default (**0.385** kg CO2e/kWh) unless you override it with a vendor-specific figure—so **net CO2e (cloud − local)** in [tools/cost_calc.py](tools/cost_calc.py) is a transparent “what-if” for reporting, not a regulatory verdict.
- **Savings:** The calculator compares **API + bandwidth** estimates against **local electricity** and shows **vendor card rates** (**$31.50/hr** cloud vs **$0.02/hr** local wall-clock, from the same compliance doc) so labs can narrate **cost and carbon** together.

Run an example:

```bash
python3 tools/cost_calc.py -n 5000 --region Kenya
```

Update **only** the human tables and the embedded JSON block in `docs/compliance_benchmarks.md` when your auditor or vendor supplies new signed values; `cost_calc` reads that file as the single official source for those inputs.

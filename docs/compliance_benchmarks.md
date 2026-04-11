# Compliance benchmarks (2026)

Official figures for **grid carbon intensity**, **vendor compute pricing**, and **default cost-model assumptions** used by BioSafety Africa tooling (notably `tools/cost_calc.py`). Replace values only when your auditor or vendor provides updated, signed disclosures; keep the machine-readable block below in sync.

## Purpose

- Support **sustainability reporting** (kg CO2e from electrical energy).
- Support **economic comparison** between US-oriented cloud GPU services and **local CPU** workflows in African laboratories (“African Lab Advantage”).

These numbers are **modeling inputs**, not legal or regulatory determinations.

## 2026 audited grid factors (kg CO2e per kWh)

Electricity grid emission factors for **scope 2–style** reporting when multiply by **kWh** of compute-related consumption.

| Region / market | kg CO2e / kWh | Notes |
|-----------------|---------------|--------|
| Kenya | 0.14 | 2026 audited planning value for local lab scenario |
| Angola | 0.24 | 2026 audited planning value |
| Nigeria | 0.48 | 2026 audited planning value |
| South Africa | 0.89 | 2026 audited planning value |

The alias **SA** in code maps to **South Africa**.

## Cloud default grid factor (US-style API hosting)

When the cloud vendor does not publish a location-specific emission factor, the model uses a **default** factor for the “Cloud (US API)” column:

| Parameter | Value (kg CO2e / kWh) |
|-----------|------------------------|
| Cloud default (illustrative US-average-style) | 0.385 |

Prefer **vendor-specific** factors from the provider’s sustainability report when available.

## 2026 vendor pricing (USD per wall-clock hour)

Rates used for **vendor compute @ card** lines in `cost_calc` (same wall-clock hours as the local CPU scenario, for comparison).

| Tier | USD / hour |
|------|------------|
| Cloud (US GPU API class) | 31.50 |
| Local (managed / amortized laptop-class CPU) | 0.02 |

## Default cost-model assumptions (non-audited)

These defaults structure API-fee and bandwidth estimates; tune to your invoices.

| Parameter | Default |
|-----------|---------|
| Cloud API fee | $0.01 / sequence |
| Bandwidth | $0.12 / GB |
| HTTP overhead | 768 bytes / request |
| Laptop draw (local embed) | 30 W |
| Local retail electricity (illustrative) | $0.22 / kWh |
| Implied cloud energy | 0.003 kWh / sequence |

---

## Machine-readable source (do not remove)

`tools/cost_calc.py` parses the JSON inside the fenced block below. **Edit the JSON when figures change**, then update the tables above to match.

```compliance-benchmarks
{
  "schema_version": "1.0",
  "audit_year": 2026,
  "grid_emissions_kg_co2e_per_kwh": {
    "Kenya": 0.14,
    "Angola": 0.24,
    "Nigeria": 0.48,
    "South Africa": 0.89
  },
  "cloud_default_grid_kg_co2e_per_kwh": 0.385,
  "vendor_pricing_usd_per_hour": {
    "cloud": 31.5,
    "local": 0.02
  },
  "cost_model_defaults": {
    "cloud_api_usd_per_sequence": 0.01,
    "bandwidth_usd_per_gb": 0.12,
    "http_overhead_bytes": 768,
    "laptop_watts": 30.0,
    "electricity_usd_per_kwh": 0.22,
    "cloud_kwh_per_sequence": 0.003
  }
}
```

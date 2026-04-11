#!/usr/bin/env python3
"""
Estimate cost and CO2e for local CPU embedding (African lab) vs US cloud GPU API.

Uses :data:`src.engine.REFERENCE_EMBED_SECONDS_PER_SEQUENCE` or a live
:func:`src.engine.benchmark_embed_seconds_per_sequence` for timing.

**Official figures** (2026 grid factors, vendor rates, cost defaults) load from
``docs/compliance_benchmarks.md`` (JSON inside the ``compliance-benchmarks`` fenced
block). See that file for audit context and tables.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.engine import (  # noqa: E402
    REFERENCE_EMBED_SECONDS_PER_SEQUENCE,
    benchmark_embed_seconds_per_sequence,
)

COMPLIANCE_BENCHMARKS_PATH = ROOT / "docs" / "compliance_benchmarks.md"
_COMPLIANCE_JSON_BLOCK = re.compile(
    r"```compliance-benchmarks\n(.*?)```", re.DOTALL
)

# Last-resort mirror of docs/compliance_benchmarks.md if the file or block is missing
_BUILTIN_COMPLIANCE: dict[str, Any] = {
    "schema_version": "1.0",
    "audit_year": 2026,
    "grid_emissions_kg_co2e_per_kwh": {
        "Kenya": 0.14,
        "Angola": 0.24,
        "Nigeria": 0.48,
        "South Africa": 0.89,
    },
    "cloud_default_grid_kg_co2e_per_kwh": 0.385,
    "vendor_pricing_usd_per_hour": {"cloud": 31.5, "local": 0.02},
    "cost_model_defaults": {
        "cloud_api_usd_per_sequence": 0.01,
        "bandwidth_usd_per_gb": 0.12,
        "http_overhead_bytes": 768,
        "laptop_watts": 30.0,
        "electricity_usd_per_kwh": 0.22,
        "cloud_kwh_per_sequence": 0.003,
    },
}


def load_compliance_benchmarks_document() -> dict[str, Any]:
    """Parse the machine-readable JSON embedded in docs/compliance_benchmarks.md."""
    if not COMPLIANCE_BENCHMARKS_PATH.is_file():
        warnings.warn(
            f"Missing {COMPLIANCE_BENCHMARKS_PATH}; using built-in compliance fallback.",
            stacklevel=2,
        )
        return dict(_BUILTIN_COMPLIANCE)
    text = COMPLIANCE_BENCHMARKS_PATH.read_text(encoding="utf-8")
    m = _COMPLIANCE_JSON_BLOCK.search(text)
    if not m:
        warnings.warn(
            "docs/compliance_benchmarks.md has no ```compliance-benchmarks``` block; "
            "using built-in fallback.",
            stacklevel=2,
        )
        return dict(_BUILTIN_COMPLIANCE)
    try:
        return json.loads(m.group(1).strip())
    except json.JSONDecodeError as exc:
        warnings.warn(
            f"Invalid compliance JSON ({exc}); using built-in fallback.",
            stacklevel=2,
        )
        return dict(_BUILTIN_COMPLIANCE)


def _build_registry(data: dict[str, Any]) -> tuple[
    dict[str, float],
    dict[str, float],
    dict[str, dict[str, float | str]],
    float,
    dict[str, float | int],
]:
    audit_year = str(data.get("audit_year", "2026"))
    grid_src = data["grid_emissions_kg_co2e_per_kwh"]
    grid_emissions: dict[str, float] = {k: float(v) for k, v in grid_src.items()}
    if "South Africa" in grid_emissions:
        grid_emissions["SA"] = grid_emissions["South Africa"]

    vp = data["vendor_pricing_usd_per_hour"]
    vendor_pricing: dict[str, float] = {
        "cloud_usd_per_hr": float(vp["cloud"]),
        "local_usd_per_hr": float(vp["local"]),
    }

    cloud_default = float(data["cloud_default_grid_kg_co2e_per_kwh"])

    raw_defaults = data["cost_model_defaults"]
    cost_defaults: dict[str, float | int] = {
        "cloud_api_usd_per_sequence": float(raw_defaults["cloud_api_usd_per_sequence"]),
        "bandwidth_usd_per_gb": float(raw_defaults["bandwidth_usd_per_gb"]),
        "http_overhead_bytes": int(raw_defaults["http_overhead_bytes"]),
        "laptop_watts": float(raw_defaults["laptop_watts"]),
        "electricity_usd_per_kwh": float(raw_defaults["electricity_usd_per_kwh"]),
        "cloud_kwh_per_sequence": float(raw_defaults["cloud_kwh_per_sequence"]),
    }

    regions: dict[str, dict[str, float | str]] = {}
    for name in ("Kenya", "Angola", "Nigeria", "South Africa"):
        regions[name] = {
            "grid_kg_co2e_per_kwh": grid_emissions[name],
            "local_usd_per_hr": vendor_pricing["local_usd_per_hr"],
            "audit_year": audit_year,
        }
    regions["Cloud_US"] = {
        "grid_kg_co2e_per_kwh": cloud_default,
        "cloud_usd_per_hr": vendor_pricing["cloud_usd_per_hr"],
        "audit_year": audit_year,
        "note": "Use vendor sustainability report when available; else default cloud grid intensity from compliance doc.",
    }

    return grid_emissions, vendor_pricing, regions, cloud_default, cost_defaults


_COMPLIANCE_DATA = load_compliance_benchmarks_document()
COMPLIANCE_SCHEMA_VERSION = str(_COMPLIANCE_DATA.get("schema_version", "?"))

(
    GRID_EMISSIONS,
    VENDOR_PRICING,
    REGIONS,
    CLOUD_GRID_KG_CO2E_PER_KWH_2026,
    COST_MODEL_DEFAULTS,
) = _build_registry(_COMPLIANCE_DATA)


def sustainability_report(
    *,
    energy_kwh: float,
    grid_kg_co2e_per_kwh: float,
    runtime_hours: float | None = None,
    power_kw: float | None = None,
    region: str | None = None,
    scenario: Literal["local", "cloud"] | None = None,
) -> dict:
    """
    Compute kg CO2e from electrical energy using an audited grid factor.

    Formula: **kg CO2e = energy_kwh × grid_kg_co2e_per_kwh**

    Parameters
    ----------
    energy_kwh
        Delivered electrical energy for the workload (kWh).
    grid_kg_co2e_per_kwh
        Location- or vendor-specific factor (kg CO2e per kWh), typically from
        ``docs/compliance_benchmarks.md``.
    runtime_hours, power_kw
        Optional provenance fields echoed in the returned dict (if provided).
    region, scenario
        Optional labels for disclosure tables.

    Returns
    -------
    dict
        Includes ``co2e_kg``, ``energy_kwh``, ``grid_kg_co2e_per_kwh``, and any
        optional metadata passed in.
    """
    if energy_kwh < 0:
        raise ValueError("energy_kwh must be non-negative")
    if grid_kg_co2e_per_kwh < 0:
        raise ValueError("grid_kg_co2e_per_kwh must be non-negative")

    co2e_kg = energy_kwh * grid_kg_co2e_per_kwh
    out: dict = {
        "co2e_kg": co2e_kg,
        "energy_kwh": energy_kwh,
        "grid_kg_co2e_per_kwh": grid_kg_co2e_per_kwh,
    }
    if runtime_hours is not None:
        out["runtime_hours"] = runtime_hours
    if power_kw is not None:
        out["power_kw"] = power_kw
    if region is not None:
        out["region"] = region
    if scenario is not None:
        out["scenario"] = scenario
    return out


def sustainability_report_for_region(
    *,
    region: str,
    scenario: Literal["local", "cloud"],
    runtime_hours: float,
    power_kw: float,
    cloud_grid_kg_co2e_per_kwh: float | None = None,
) -> dict:
    """
    Convenience wrapper: resolve grid factor from :data:`REGIONS` / :data:`GRID_EMISSIONS`
    (loaded from ``docs/compliance_benchmarks.md``), compute
    ``energy_kwh = runtime_hours × power_kw``, then :func:`sustainability_report`.

    * **local** — uses ``GRID_EMISSIONS[region]`` (Kenya, Angola, Nigeria, South Africa, SA).
    * **cloud** — uses ``cloud_grid_kg_co2e_per_kwh`` if set, else
      ``REGIONS[\"Cloud_US\"][\"grid_kg_co2e_per_kwh\"]``.
    """
    energy_kwh = runtime_hours * power_kw
    if scenario == "local":
        grid = GRID_EMISSIONS.get(region)
        if grid is None:
            raise ValueError(
                f"Unknown region {region!r}. Use one of: "
                f"{', '.join(sorted(k for k in GRID_EMISSIONS if k != 'SA'))}."
            )
        return sustainability_report(
            energy_kwh=energy_kwh,
            grid_kg_co2e_per_kwh=grid,
            runtime_hours=runtime_hours,
            power_kw=power_kw,
            region=region,
            scenario="local",
        )

    grid = (
        cloud_grid_kg_co2e_per_kwh
        if cloud_grid_kg_co2e_per_kwh is not None
        else float(REGIONS["Cloud_US"]["grid_kg_co2e_per_kwh"])
    )
    return sustainability_report(
        energy_kwh=energy_kwh,
        grid_kg_co2e_per_kwh=grid,
        runtime_hours=runtime_hours,
        power_kw=power_kw,
        region="Cloud_US",
        scenario="cloud",
    )


def vendor_compute_cost_usd(*, scenario: Literal["local", "cloud"], runtime_hours: float) -> float:
    """Wall-clock compute cost using :data:`VENDOR_PRICING` (USD/hr from compliance doc)."""
    if runtime_hours < 0:
        raise ValueError("runtime_hours must be non-negative")
    rate = (
        VENDOR_PRICING["cloud_usd_per_hr"]
        if scenario == "cloud"
        else VENDOR_PRICING["local_usd_per_hr"]
    )
    return runtime_hours * rate


def parse_fasta(path: Path) -> list[str]:
    """Return amino-acid sequences (uppercase string per record)."""
    seqs: list[str] = []
    header: str | None = None
    parts: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    seqs.append("".join(parts).upper().replace(" ", ""))
                header = line[1:]
                parts = []
            else:
                parts.append(line)
    if header is not None:
        seqs.append("".join(parts).upper().replace(" ", ""))
    return [s for s in seqs if s]


def estimate_payload_bytes(sequences: list[str], overhead_per_request: int) -> int:
    """Rough HTTPS JSON/FASTA upload + small response allowance."""
    body = sum(len(s.encode("utf-8")) for s in sequences)
    return body + overhead_per_request * len(sequences)


def fmt_usd(x: float) -> str:
    ax = abs(x)
    if ax >= 1000:
        return f"${x:,.2f}"
    if ax >= 1.0:
        return f"${x:,.2f}"
    if ax == 0.0:
        return "$0.00"
    return f"${x:,.4f}"


def fmt_kwh(x: float) -> str:
    return f"{x:,.4f}"


def fmt_kg(x: float) -> str:
    ax = abs(x)
    if ax == 0.0:
        return "0.00"
    if ax < 0.01:
        return f"{x:,.4f}"
    return f"{x:,.2f}"


def print_table(rows: list[tuple[str, str, str]], title: str) -> None:
    c0 = max(len(r[0]) for r in rows)
    c1 = max(len(r[1]) for r in rows)
    c2 = max(len(r[2]) for r in rows)
    w = c0 + c1 + c2 + 6
    print(title)
    print("-" * w)
    print(f"  {rows[0][0]:<{c0}}  {rows[0][1]:>{c1}}  {rows[0][2]:>{c2}}")
    print("-" * w)
    for r in rows[1:]:
        print(f"  {r[0]:<{c0}}  {r[1]:>{c1}}  {r[2]:>{c2}}")
    print("-" * w)


def main() -> None:
    d = COST_MODEL_DEFAULTS
    p = argparse.ArgumentParser(
        description="Compare cloud GPU API vs local CPU embedding cost & CO2e (illustrative)."
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "-n",
        "--num-sequences",
        type=int,
        metavar="N",
        help="Number of sequences (synthetic count for cost model).",
    )
    src.add_argument(
        "--fasta",
        type=Path,
        help="FASTA file; cost model uses record count and total sequence length.",
    )

    p.add_argument(
        "--region",
        type=str,
        default="Kenya",
        help=(
            "Local grid region for CO2e (2026 audited): Kenya, Angola, Nigeria, "
            "South Africa, SA (default: Kenya)."
        ),
    )
    p.add_argument(
        "--benchmark",
        action="store_true",
        help=(
            "Run src.engine.benchmark_embed_seconds_per_sequence() on this machine "
            "(loads ESM-2 8M; slow first run)."
        ),
    )
    p.add_argument(
        "--seconds-per-sequence",
        type=float,
        default=None,
        metavar="SEC",
        help=(
            "Override CPU seconds per sequence. Default: engine reference or --benchmark."
        ),
    )

    p.add_argument(
        "--cloud-api-usd-per-sequence",
        type=float,
        default=d["cloud_api_usd_per_sequence"],
        help=(
            "Cloud vendor charge per sequence "
            f"(default: {d['cloud_api_usd_per_sequence']} from compliance doc)."
        ),
    )
    p.add_argument(
        "--bandwidth-usd-per-gb",
        type=float,
        default=d["bandwidth_usd_per_gb"],
        help=(
            "Estimated egress/ingress cost per GB for API traffic "
            f"(default: {d['bandwidth_usd_per_gb']} from compliance doc)."
        ),
    )
    p.add_argument(
        "--http-overhead-bytes",
        type=int,
        default=d["http_overhead_bytes"],
        help=(
            "Extra bytes per request (headers/JSON envelope) "
            f"(default: {d['http_overhead_bytes']} from compliance doc)."
        ),
    )

    p.add_argument(
        "--laptop-watts",
        type=float,
        default=d["laptop_watts"],
        help=(
            "Assumed average CPU package / system draw during embed "
            f"(default: {d['laptop_watts']} W from compliance doc)."
        ),
    )
    p.add_argument(
        "--electricity-usd-per-kwh",
        type=float,
        default=d["electricity_usd_per_kwh"],
        help=(
            "Local retail tariff "
            f"(default: {d['electricity_usd_per_kwh']} USD/kWh from compliance doc)."
        ),
    )

    p.add_argument(
        "--cloud-kwh-per-sequence",
        type=float,
        default=d["cloud_kwh_per_sequence"],
        help=(
            "Implied datacenter energy per API sequence incl. GPU share & PUE "
            f"(default: {d['cloud_kwh_per_sequence']} kWh from compliance doc)."
        ),
    )
    p.add_argument(
        "--cloud-grid-kg-co2-per-kwh",
        type=float,
        default=None,
        help=(
            f"Cloud region grid factor kg CO2e/kWh (default: {CLOUD_GRID_KG_CO2E_PER_KWH_2026})."
        ),
    )
    p.add_argument(
        "--local-grid-kg-co2-per-kwh",
        type=float,
        default=None,
        help="Override local grid factor; default uses GRID_EMISSIONS[--region].",
    )

    args = p.parse_args()

    cloud_grid = (
        args.cloud_grid_kg_co2_per_kwh
        if args.cloud_grid_kg_co2_per_kwh is not None
        else CLOUD_GRID_KG_CO2E_PER_KWH_2026
    )

    local_grid = (
        args.local_grid_kg_co2_per_kwh
        if args.local_grid_kg_co2_per_kwh is not None
        else GRID_EMISSIONS.get(args.region)
    )
    if local_grid is None:
        print(
            f"Unknown --region {args.region!r}. Choose from "
            f"{', '.join(sorted(k for k in GRID_EMISSIONS if k != 'SA'))} or SA.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.fasta:
        sequences = parse_fasta(args.fasta)
        n = len(sequences)
        if n == 0:
            print("No sequences found in FASTA.", file=sys.stderr)
            sys.exit(1)
    else:
        assert args.num_sequences is not None
        n = args.num_sequences
        if n <= 0:
            print("N must be positive.", file=sys.stderr)
            sys.exit(1)
        sequences = ["M" * 256] * n

    if args.seconds_per_sequence is not None:
        sec_per_seq = args.seconds_per_sequence
        sec_note = "user override"
    elif args.benchmark:
        mean_t, stdev_t = benchmark_embed_seconds_per_sequence()
        sec_per_seq = mean_t
        sec_note = f"benchmark mean ± sd: {mean_t:.3f} ± {stdev_t:.3f} s"
    else:
        sec_per_seq = REFERENCE_EMBED_SECONDS_PER_SEQUENCE
        sec_note = f"engine reference ({REFERENCE_EMBED_SECONDS_PER_SEQUENCE} s/seq)"

    total_compute_hours = n * sec_per_seq / 3600.0
    power_kw = args.laptop_watts / 1000.0
    local_kwh = power_kw * total_compute_hours
    local_electricity_usd = local_kwh * args.electricity_usd_per_kwh

    payload_b = estimate_payload_bytes(sequences, args.http_overhead_bytes)
    bandwidth_gb = payload_b / (1024**3)
    bandwidth_usd = bandwidth_gb * args.bandwidth_usd_per_gb
    api_usd = n * args.cloud_api_usd_per_sequence
    cloud_total_usd = api_usd + bandwidth_usd

    cloud_kwh_total = n * args.cloud_kwh_per_sequence
    local_report = sustainability_report(
        energy_kwh=local_kwh,
        grid_kg_co2e_per_kwh=local_grid,
        runtime_hours=total_compute_hours,
        power_kw=power_kw,
        region=args.region,
        scenario="local",
    )
    cloud_report = sustainability_report(
        energy_kwh=cloud_kwh_total,
        grid_kg_co2e_per_kwh=cloud_grid,
        scenario="cloud",
        region="Cloud_US",
    )
    co2_cloud_kg = float(cloud_report["co2e_kg"])
    co2_local_kg = float(local_report["co2e_kg"])
    co2_avoided_kg = co2_cloud_kg - co2_local_kg

    savings_usd = cloud_total_usd - local_electricity_usd

    vendor_cloud_usd = vendor_compute_cost_usd(
        scenario="cloud", runtime_hours=total_compute_hours
    )
    vendor_local_usd = vendor_compute_cost_usd(
        scenario="local", runtime_hours=total_compute_hours
    )

    print()
    print("  African Lab Advantage — cost & footprint (illustrative model)")
    print(f"  Sequences: {n:,}  |  CPU timing: {sec_note}")
    print(
        f"  Local grid ({args.region}): {local_grid:g} kg CO2e/kWh (2026 audited)  |  "
        f"Cloud grid: {cloud_grid:g} kg CO2e/kWh"
    )
    print()

    print_table(
        [
            ("Line item", "Cloud (US API)", "Local (laptop CPU)"),
            (
                "API / compute fee",
                fmt_usd(api_usd),
                "—",
            ),
            (
                "Bandwidth (est.)",
                fmt_usd(bandwidth_usd),
                "—",
            ),
            (
                "Electricity",
                "—",
                fmt_usd(local_electricity_usd),
            ),
            (
                "Vendor compute @ card (wall-clock)",
                fmt_usd(vendor_cloud_usd),
                fmt_usd(vendor_local_usd),
            ),
            (
                "Subtotal (API+bw / elec. only)",
                fmt_usd(cloud_total_usd),
                fmt_usd(local_electricity_usd),
            ),
            (
                "Energy (kWh)",
                fmt_kwh(cloud_kwh_total),
                fmt_kwh(local_kwh),
            ),
            (
                "CO2e (kg)",
                fmt_kg(co2_cloud_kg),
                fmt_kg(co2_local_kg),
            ),
        ],
        "",
    )

    print()
    print("  ── African Lab Advantage (summary) ──")
    print(f"    Total savings vs cloud API:     ${savings_usd:,.4f}")
    print(
        f"    Net CO2e (cloud − local):       {fmt_kg(co2_avoided_kg)} kg  "
        "(positive ⇒ lower footprint when processing locally)"
    )
    print()
    print(
        f"    Vendor rates (wall-clock): cloud ${VENDOR_PRICING['cloud_usd_per_hr']:.2f}/hr, "
        f"local ${VENDOR_PRICING['local_usd_per_hr']:.2f}/hr"
    )
    print()
    print(
        f"  Official inputs: docs/compliance_benchmarks.md "
        f"(schema {COMPLIANCE_SCHEMA_VERSION}, audit year {_COMPLIANCE_DATA.get('audit_year', '?')})."
    )
    print(
        "  Tune API, bandwidth, and cloud kWh/seq to invoices; replace cloud grid "
        "with vendor disclosures when available."
    )
    print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Offline asset helper: ESM-2 8M snapshot, manifest (SHA + timestamp), Pfam HMMs.

Called from deployment/offline_setup.sh. Can also run standalone:

  python3 deployment/offline_setup_helpers.py --all
  python3 deployment/offline_setup_helpers.py --manifest-and-hmmer-only
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = REPO_ROOT / "models" / "esm2_8m"
HMMER_DIR = REPO_ROOT / "models" / "hmmer"
MODEL_ID = "facebook/esm2_t6_8M_UR50D"

# Starter “common vector backbone” markers (Tier 1, non-AI). Pfam accessions via EBI InterPro.
HMM_PROFILES: list[tuple[str, str, str]] = [
    (
        "PF13354",
        "beta_lactamase_AmpR.hmm",
        "Class A beta-lactamase / AmpR (common antibiotic resistance on cloning vectors)",
    ),
    (
        "PF02486",
        "rep_plasmid_N.hmm",
        "Plasmid replication Rep protein N-terminal domain",
    ),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_esm_snapshot() -> None:
    from huggingface_hub import snapshot_download

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=str(MODEL_DIR),
    )


def collect_file_shas(model_dir: Path) -> dict[str, str]:
    """SHA-256 for tokenizer + config + weight files."""
    names: list[str] = []
    for pattern in (
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.txt",
        "added_tokens.json",
    ):
        p = model_dir / pattern
        if p.is_file():
            names.append(pattern)
    for p in sorted(model_dir.glob("*.safetensors")):
        names.append(p.name)
    for p in sorted(model_dir.glob("pytorch_model.bin")):
        names.append(p.name)
    if not names:
        raise FileNotFoundError(
            f"No known model files under {model_dir}. Run ESM download first."
        )
    return {n: sha256_file(model_dir / n) for n in names}


def write_manifest(model_dir: Path = MODEL_DIR) -> None:
    fps = collect_file_shas(model_dir)
    body = json.dumps(fps, sort_keys=True, separators=(",", ":"))
    manifest_sha256 = hashlib.sha256(body.encode("utf-8")).hexdigest()
    manifest = {
        "model_id": MODEL_ID,
        "download_timestamp_utc": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "files_sha256": fps,
        "manifest_sha256": manifest_sha256,
    }
    out = model_dir / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


def download_pfam_hmm(accession: str, dest: Path) -> None:
    url = f"https://www.ebi.ac.uk/interpro/api/entry/pfam/{accession}?annotation=hmm"
    req = urllib.request.Request(url, headers={"Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read()
    data = gzip.decompress(raw)
    dest.write_bytes(data)
    print(f"Downloaded {accession} -> {dest}")


def write_hmmer_readme() -> None:
    lines = [
        "# Common vector backbone markers (Tier 1 HMMER)",
        "",
        "Pfam HMMs from [EBI InterPro](https://www.ebi.ac.uk/interpro/) "
        "(gzip payload decompressed). **Not** a substitute for regulated "
        "select-agent screening — indicative markers only.",
        "",
        "```bash",
        "hmmscan --domtblout hits.domtblout models/hmmer/*.hmm query.pep.fa",
        "```",
        "",
    ]
    for acc, fname, desc in HMM_PROFILES:
        lines.append(f"- `{fname}` — {desc} (`{acc}`)")
    (HMMER_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def download_hmmer_profiles() -> None:
    HMMER_DIR.mkdir(parents=True, exist_ok=True)
    for acc, fname, _desc in HMM_PROFILES:
        download_pfam_hmm(acc, HMMER_DIR / fname)
    write_hmmer_readme()
    print(f"HMMER profiles in {HMMER_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline ESM + manifest + HMMER setup")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download ESM snapshot, write manifest, download HMM profiles",
    )
    parser.add_argument(
        "--manifest-and-hmmer-only",
        action="store_true",
        help="Assume ESM files already present; manifest + HMM only",
    )
    args = parser.parse_args()

    if args.all:
        download_esm_snapshot()
        write_manifest()
        download_hmmer_profiles()
    elif args.manifest_and_hmmer_only:
        write_manifest()
        download_hmmer_profiles()
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()

"""
Lite embedding engine (CPU-only).

Derived from funcscreen ``train_detector_cv.py``, ``rebuild_embeddings.py``,
and ``attribution.py``. Uses residue-only mean pooling (attribution v2.0) for
embedding semantics aligned with the funcscreen screening pipeline.

* Model: ``facebook/esm2_t6_8M_UR50D`` (~8M parameters).
* Offline: if ``MODEL_DIR`` (env) or ``<repo>/models/esm2_8m`` contains a snapshot
  (with ``config.json``), loads from disk with ``local_files_only=True`` — no Hub fetch.
* Device: **CPU only** — hard-coded so runs never depend on GPU/MPS.
* RAM: :meth:`LiteEngine.streaming_embed` yields incrementally with micro-batches
  of at most 4 sequences.
* Storage: :meth:`LiteEngine.quantize_embeddings` optional float16 / int8
  quantization for compact local fingerprint stores.
* Audit: JSONL logging of ``sequence_hash`` and ``model_version`` for traceability.

650M-trained classifiers (1280-d) are not compatible with 320-d 8M embeddings
without retraining.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import statistics
import time
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Literal, Sequence

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

# ESM-2 context: 1022 residues + BOS/EOS in the tokenizer (funcscreen convention).
MODEL_NAME = "facebook/esm2_t6_8M_UR50D"
MAX_SEQ_LEN = 1022
# Hard-coded CPU — no CUDA/MPS branch (avoids crashes on GPU-less hardware).
DEVICE: Literal["cpu"] = "cpu"
STREAM_BATCH_MAX = 4
ENGINE_VERSION = "0.2.0"

# Order-of-magnitude CPU latency for planning when no live benchmark is run
# (ESM-2 8M, single-sequence batch, ~256 aa on a typical laptop-class CPU).
REFERENCE_EMBED_SECONDS_PER_SEQUENCE = 0.42

REPO_ROOT = Path(__file__).resolve().parent.parent
OFFLINE_MODEL_DIR = REPO_ROOT / "models" / "esm2_8m"

warnings.filterwarnings("ignore", category=UserWarning, module="transformers")


def _is_local_model_dir(path: Path) -> bool:
    return path.is_dir() and (path / "config.json").is_file()


def _audit_version_for_local_dir(model_dir: Path) -> str:
    manifest = model_dir / "manifest.json"
    if manifest.is_file():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            parts = [str(data.get("model_id", MODEL_NAME)), "offline"]
            msha = data.get("manifest_sha256")
            if msha:
                parts.append(f"manifest_sha256={msha}")
            ts = data.get("download_timestamp_utc")
            if ts:
                parts.append(f"downloaded={ts}")
            return " | ".join(parts)
        except (json.JSONDecodeError, OSError):
            pass
    return f"{MODEL_NAME}@local:{model_dir.resolve()}"


def resolve_esm2_load_spec(model_name: str | None = None) -> tuple[str, str, bool]:
    """
    Pick HuggingFace id vs local directory for ``from_pretrained``.

    Returns ``(load_target, audit_model_version, local_files_only)``.

    Resolution when ``model_name`` is ``None`` or the default hub id
    :data:`MODEL_NAME`:

    1. ``MODEL_DIR`` environment variable (directory with ``config.json``)
    2. :data:`OFFLINE_MODEL_DIR` if it contains ``config.json``
    3. Else Hub id :data:`MODEL_NAME`

    Any other ``model_name`` is treated as an explicit Hub id or absolute/relative
    path to a model directory.
    """
    if model_name is not None and model_name != MODEL_NAME:
        p = Path(model_name)
        if _is_local_model_dir(p):
            rp = p.resolve()
            return str(rp), _audit_version_for_local_dir(rp), True
        return model_name, model_name, False

    env = (os.environ.get("MODEL_DIR") or "").strip()
    if env:
        ep = Path(env)
        if _is_local_model_dir(ep):
            rp = ep.resolve()
            return str(rp), _audit_version_for_local_dir(rp), True

    if _is_local_model_dir(OFFLINE_MODEL_DIR):
        rp = OFFLINE_MODEL_DIR.resolve()
        return str(rp), _audit_version_for_local_dir(rp), True

    return MODEL_NAME, MODEL_NAME, False


def sequence_sha256(sequence: str) -> str:
    """SHA-256 hex digest of the sequence bytes (UTF-8); no raw sequence in logs."""
    return hashlib.sha256(sequence.encode("utf-8")).hexdigest()


def append_fair_audit_log(path: str | Path, record: dict) -> None:
    """
    Append one JSON object per line (JSONL) for audit trails.

    Typical keys: ``sequence_hash``, ``model_version``, ``event``;
    ``ts`` (UTC ISO8601) is added automatically.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {
        **record,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, sort_keys=True) + "\n")


def _residue_mask(attention_mask: torch.Tensor) -> torch.Tensor:
    """
    Residue-only mask from funcscreen ``attribution.py`` (v2.0): zero [CLS]
    (position 0) and the last non-pad token (EOS) before mean-pooling.
    """
    m = attention_mask.clone().float()
    m[:, 0] = 0.0
    for j in range(m.shape[0]):
        seq_len = int(attention_mask[j].sum().item())
        if seq_len > 1:
            m[j, seq_len - 1] = 0.0
    return m


def _mean_pool(hidden: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    mask = mask.unsqueeze(-1)
    summed = (hidden * mask).sum(dim=1)
    denom = mask.sum(dim=1).clamp(min=1e-9)
    return summed / denom


@dataclass
class LiteEngine:
    """
    Load ESM-2 8M on CPU; embed with residue-only pooling.

    ``batch_size`` is capped at :data:`STREAM_BATCH_MAX` (4) to bound activation RAM.
    """

    model_name: str = MODEL_NAME
    batch_size: int = 4
    num_threads: int | None = None
    embedding_dim: int = field(init=False)
    model_version: str = field(init=False)

    def __post_init__(self) -> None:
        if self.num_threads is not None:
            torch.set_num_threads(int(self.num_threads))

        self.batch_size = max(1, min(STREAM_BATCH_MAX, int(self.batch_size)))
        self._device = torch.device(DEVICE)
        load_target, self.model_version, local_only = resolve_esm2_load_spec(
            self.model_name
        )
        self._load_target = load_target
        self._tokenizer = AutoTokenizer.from_pretrained(
            load_target, local_files_only=local_only
        )
        self._model = AutoModel.from_pretrained(
            load_target, local_files_only=local_only
        )
        self._model.to(self._device)
        self._model.eval()

        self.embedding_dim = int(self._model.config.hidden_size)

    def embed_batch(self, sequences: Sequence[str]) -> np.ndarray:
        """Return float32 array ``(N, embedding_dim)`` using residue-only pooling."""
        if not sequences:
            return np.zeros((0, self.embedding_dim), dtype=np.float32)

        out: list[np.ndarray] = []
        n = len(sequences)
        bs = self.batch_size

        with torch.inference_mode():
            for start in range(0, n, bs):
                chunk = [s[:MAX_SEQ_LEN] for s in sequences[start : start + bs]]
                inputs = self._tokenizer(
                    chunk,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=MAX_SEQ_LEN + 2,
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}
                outputs = self._model(**inputs)
                rmask = _residue_mask(inputs["attention_mask"])
                pooled = _mean_pool(outputs.last_hidden_state, rmask)
                out.append(pooled.numpy().astype(np.float32, copy=False))

        return np.vstack(out)

    def embed(self, sequence: str) -> np.ndarray:
        """Single sequence, shape ``(embedding_dim,)``."""
        return self.embed_batch([sequence[:MAX_SEQ_LEN]])[0]

    def streaming_embed(
        self,
        sequences: Iterable[str],
        *,
        micro_batch: int = 1,
        audit_log: str | Path | None = None,
    ) -> Iterator[tuple[str, np.ndarray]]:
        """
        Yield ``(sequence_hash, embedding)`` without holding all embeddings in memory.

        ``micro_batch`` is clamped to 1..4. Internally runs forward in chunks of
        that size, then yields one row at a time.

        If ``audit_log`` is set, each yielded sequence appends a JSONL record with
        ``sequence_hash``, ``model_version``, ``engine_version``, and ``event``.
        """
        if isinstance(sequences, (str, bytes)):
            raise TypeError(
                "streaming_embed expects an iterable of sequence strings, not a single str/bytes"
            )

        mb = max(1, min(STREAM_BATCH_MAX, int(micro_batch)))
        log_path = Path(audit_log) if audit_log is not None else None

        def flush(buf: list[str]) -> Iterator[tuple[str, np.ndarray]]:
            if not buf:
                return
            embs = self.embed_batch(buf)
            for seq, row in zip(buf, embs, strict=True):
                h = sequence_sha256(seq)
                if log_path is not None:
                    append_fair_audit_log(
                        log_path,
                        {
                            "event": "embedding_complete",
                            "sequence_hash": h,
                            "model_version": self.model_version,
                            "engine_version": ENGINE_VERSION,
                            "embedding_dim": self.embedding_dim,
                        },
                    )
                yield h, row.copy()

        it = iter(sequences)
        buf: list[str] = []
        while True:
            try:
                while len(buf) < mb:
                    buf.append(next(it)[:MAX_SEQ_LEN])
            except StopIteration:
                yield from flush(buf)
                return
            yield from flush(buf)
            buf = []

    @staticmethod
    def quantize_embeddings(
        embeddings: np.ndarray,
        *,
        precision: Literal["float16", "int8"] = "float16",
    ) -> dict:
        """
        Compress embeddings for local storage (smaller footprint).

        * ``float16``: lossy half precision; returns ``{"data", "dtype"}``.
        * ``int8``: symmetric scale; returns ``{"data", "dtype", "scale"}`` where
          ``data`` is int8 and approximate dequant is ``data.astype(float32) * scale``.

        ``embeddings`` may be 1-D (single vector) or 2-D (batch).
        """
        x = np.asarray(embeddings, dtype=np.float32)
        if precision == "float16":
            return {"data": x.astype(np.float16), "dtype": "float16"}
        if precision == "int8":
            amax = float(np.max(np.abs(x)))
            scale = amax / 127.0 + 1e-8
            q = np.clip(np.round(x / scale), -128, 127).astype(np.int8)
            return {"data": q, "dtype": "int8", "scale": scale}
        raise ValueError(f"precision must be 'float16' or 'int8', got {precision!r}")

    @staticmethod
    def dequantize_embeddings(bundle: dict) -> np.ndarray:
        """Invert :meth:`quantize_embeddings` (float16 or int8)."""
        dtype = bundle["dtype"]
        data = np.asarray(bundle["data"])
        if dtype == "float16":
            return data.astype(np.float32)
        if dtype == "int8":
            scale = float(bundle["scale"])
            return data.astype(np.float32) * scale
        raise ValueError(f"unknown dtype {dtype!r}")


def benchmark_embed_seconds_per_sequence(
    *,
    n_warmup: int = 1,
    n_trials: int = 8,
    seq_len: int = 256,
    batch_size: int = 1,
    model_name: str | None = None,
    seed: int = 42,
) -> tuple[float, float]:
    """
    Wall-clock seconds per sequence for :class:`LiteEngine` on this machine.

    Returns ``(mean_seconds, stdev_seconds)`` over ``n_trials`` ``embed`` calls
    after ``n_warmup`` warmup iterations. Sequences are random valid amino-acid
    strings of length ``seq_len``.
    """
    rng = random.Random(seed)
    alphabet = "ACDEFGHIKLMNPQRSTVWY"

    def rand_seq(n: int) -> str:
        return "".join(rng.choice(alphabet) for _ in range(n))

    need = n_warmup + n_trials
    seqs = [rand_seq(seq_len) for _ in range(need)]

    mn = MODEL_NAME if model_name is None else model_name
    engine = LiteEngine(model_name=mn, batch_size=batch_size)

    for i in range(n_warmup):
        engine.embed(seqs[i])

    samples: list[float] = []
    for i in range(n_trials):
        t0 = time.perf_counter()
        engine.embed(seqs[n_warmup + i])
        samples.append(time.perf_counter() - t0)

    mean_t = statistics.mean(samples)
    dev = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return mean_t, dev


def embed_sequences(
    sequences: Sequence[str],
    *,
    batch_size: int = 4,
    num_threads: int | None = None,
    model_name: str | None = None,
) -> np.ndarray:
    """
    One-shot embed (loads model). ``batch_size`` is capped at 4.

    ``model_name`` default ``None`` uses the same resolution as :class:`LiteEngine`
    (``MODEL_DIR`` / ``models/esm2_8m`` / Hub).
    """
    mn = MODEL_NAME if model_name is None else model_name
    engine = LiteEngine(
        model_name=mn,
        batch_size=batch_size,
        num_threads=num_threads,
    )
    return engine.embed_batch(sequences)


__all__ = [
    "DEVICE",
    "ENGINE_VERSION",
    "LiteEngine",
    "MODEL_NAME",
    "MAX_SEQ_LEN",
    "OFFLINE_MODEL_DIR",
    "REFERENCE_EMBED_SECONDS_PER_SEQUENCE",
    "STREAM_BATCH_MAX",
    "append_fair_audit_log",
    "benchmark_embed_seconds_per_sequence",
    "embed_sequences",
    "resolve_esm2_load_spec",
    "sequence_sha256",
]


if __name__ == "__main__":
    import argparse

    def _parse_fasta_cli(path: Path) -> list[str]:
        seqs: list[str] = []
        hdr: str | None = None
        parts: list[str] = []
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    if hdr is not None:
                        seqs.append("".join(parts).upper().replace(" ", ""))
                    hdr, parts = line[1:], []
                else:
                    parts.append(line)
        if hdr is not None:
            seqs.append("".join(parts).upper().replace(" ", ""))
        return [s for s in seqs if s]

    ap = argparse.ArgumentParser(
        description="CPU-only ESM-2 8M embedding (run from repo root)."
    )
    # Group to make -s and -f mutually exclusive for clarity
    group = ap.add_mutually_exclusive_group()
    group.add_argument(
        "--sequence",
        "-s",
        help="Single amino-acid sequence to embed.",
    )
    group.add_argument(
        "--fasta",
        "-f",
        type=Path,
        help="FASTA file to embed.",
    )
    ap.add_argument(
        "--audit-log",
        "-a",
        type=Path,
        help="Path to save the JSONL audit trail.",
    )

    args = ap.parse_args()
    eng = LiteEngine()

    # Determine input list
    if args.fasta:
        input_seqs = _parse_fasta_cli(args.fasta)
    else:
        input_seqs = [args.sequence or "MKTAYIAKQRQISFVKSHFSRQ"]

    # Use streaming_embed to handle the audit log correctly
    results = list(eng.streaming_embed(input_seqs, audit_log=args.audit_log))

    print(f"✅ Processed {len(results)} sequences.")
    print(f"📊 Embedding Shape: ({len(results)}, {eng.embedding_dim})")
    if args.audit_log:
        print(f"📜 Audit trail saved to: {args.audit_log}")

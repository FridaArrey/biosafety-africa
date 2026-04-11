#!/usr/bin/env bash
# Download ESM-2 8M + tokenizer offline, write manifest, fetch starter HMMER profiles.
# Run from anywhere:  bash deployment/offline_setup.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODEL_ID="facebook/esm2_t6_8M_UR50D"
DEST="models/esm2_8m"

mkdir -p "$DEST" models/hmmer

if command -v hf >/dev/null 2>&1; then
  echo "==> Downloading ${MODEL_ID} with hf download -> ${DEST}"
  hf download "${MODEL_ID}" --local-dir "${DEST}"
  echo "==> Writing manifest.json and Tier-1 HMMER profiles"
  python3 "${ROOT}/deployment/offline_setup_helpers.py" --manifest-and-hmmer-only
elif command -v huggingface-cli >/dev/null 2>&1; then
  echo "==> Downloading ${MODEL_ID} with huggingface-cli -> ${DEST}"
  if ! huggingface-cli download "${MODEL_ID}" --local-dir "${DEST}"; then
    huggingface-cli download "${MODEL_ID}" \
      --local-dir "${DEST}" \
      --local-dir-use-symlinks false
  fi
  echo "==> Writing manifest.json and Tier-1 HMMER profiles"
  python3 "${ROOT}/deployment/offline_setup_helpers.py" --manifest-and-hmmer-only
else
  echo "==> No hf / huggingface-cli; using Python (huggingface_hub)"
  python3 "${ROOT}/deployment/offline_setup_helpers.py" --all
fi

echo "==> Offline setup complete."
echo "    ESM-2 8M:  ${ROOT}/${DEST}  (see manifest.json)"
echo "    HMMER:     ${ROOT}/models/hmmer"

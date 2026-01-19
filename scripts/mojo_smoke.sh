#!/usr/bin/env bash
set -euo pipefail

# Simple runner for MojoAudioFFI smoke test.
# Usage: scripts/mojo_smoke.sh
# Optionally activate a venv first; requires opuslib_next installed.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/main/xiaozhi-server"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi

if ! python3 - <<'PY' >/dev/null 2>&1; then
import opuslib_next  # noqa: F401
PY
then
  echo "opuslib_next not installed; install it (e.g., pip install opuslib_next) then rerun." >&2
  exit 1
fi

echo "Running MojoAudioFFI smoke test..."
python3 -m mojo.ffi.smoke_test

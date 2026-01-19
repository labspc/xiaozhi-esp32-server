#!/usr/bin/env bash
set -euo pipefail

# CI-friendly runner for MojoAudioFFI smoke test.
# - Creates a venv in /tmp/mojo-smoke-venv
# - Installs opuslib_next
# - Runs python -m mojo.ffi.smoke_test

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/main/xiaozhi-server"

VENV_DIR="/tmp/mojo-smoke-venv"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip >/dev/null
python -m pip install opuslib_next >/dev/null

echo "Running MojoAudioFFI smoke test (CI)..."
python -m mojo.ffi.smoke_test

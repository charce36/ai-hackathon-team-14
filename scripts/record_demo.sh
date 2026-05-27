#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Creating venv if needed..."
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate

echo "==> Installing Python deps..."
pip install -q -e ".[dev]"

echo "==> Building demo UI..."
cd demo-ui
npm install --silent
npm run build
cd ..

echo "==> Starting server (VIDEO_DEMO=true)..."
export VIDEO_DEMO=true
export DRY_RUN=true
export DEMO_STEP_DELAY_MS=800

python -m publisher_support.main &
PID=$!
sleep 2

echo "==> Demo available at http://localhost:8000/demo"
echo "    Press Ctrl+C to stop"

if command -v open &>/dev/null; then
  open "http://localhost:8000/demo"
fi

wait $PID

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PORT=8000

ensure_node() {
  local min_major=18
  local current_major
  current_major="$(node -v 2>/dev/null | sed 's/^v//' | cut -d. -f1 || true)"

  if [ -z "$current_major" ] || [ "$current_major" -lt "$min_major" ]; then
    if [ -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]; then
      # shellcheck source=/dev/null
      . "${NVM_DIR:-$HOME/.nvm}/nvm.sh"
      if [ -f .nvmrc ]; then
        nvm use
      else
        nvm use 20 >/dev/null 2>&1 || nvm use 18 >/dev/null 2>&1 || true
      fi
      current_major="$(node -v 2>/dev/null | sed 's/^v//' | cut -d. -f1 || true)"
    fi
  fi

  if [ -z "$current_major" ] || [ "$current_major" -lt "$min_major" ]; then
    echo "Error: Node.js >= ${min_major} requerido para build de demo-ui (actual: $(node -v 2>/dev/null || echo 'no encontrado'))" >&2
    echo "Con nvm: nvm install 20 && nvm use" >&2
    exit 1
  fi
}

port_pids() {
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -ti ":$PORT" 2>/dev/null || true)
  fi
  if [ -z "$pids" ] && command -v fuser >/dev/null 2>&1; then
    pids=$(fuser "$PORT/tcp" 2>/dev/null || true)
  fi
  # awk avoids grep exit 1 on empty input (which aborts the script with set -e)
  # shellcheck disable=SC2086
  printf '%s\n' $pids 2>/dev/null | awk '/^[0-9]+$/' | sort -u | tr '\n' ' '
}

free_port() {
  local pids
  pids=$(port_pids)
  if [ -z "$pids" ]; then
    return 0
  fi
  echo "==> Liberando puerto $PORT (PIDs: $pids)..."
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  sleep 1
  pids=$(port_pids)
  if [ -n "$pids" ]; then
    echo "==> Forzando cierre (kill -9)..."
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
    sleep 1
  fi
  if [ -n "$(port_pids)" ]; then
    echo "Error: el puerto $PORT sigue ocupado." >&2
    echo "  Probá: pids=\$(lsof -ti :$PORT); [ -n \"\$pids\" ] && kill -9 \$pids" >&2
    exit 1
  fi
}

echo "==> Creating venv if needed..."
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate

echo "==> Installing Python deps..."
pip install -q -e ".[dev]"

echo "==> Building demo UI..."
ensure_node
cd demo-ui
npm install --silent
npm run build
cd ..

echo "==> Starting server (VIDEO_DEMO=true)..."
export VIDEO_DEMO=true
export DRY_RUN=true
export DEMO_STEP_DELAY_MS=800

free_port

python -m publisher_support.main &
PID=$!

cleanup() {
  kill "$PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in 1 2 3 4 5; do
  sleep 1
  if kill -0 "$PID" 2>/dev/null && curl -sf "http://localhost:$PORT/health" >/dev/null; then
    break
  fi
done

if ! kill -0 "$PID" 2>/dev/null; then
  echo "Error: el servidor no pudo arrancar en el puerto $PORT." >&2
  free_port
  exit 1
fi

if ! curl -sf "http://localhost:$PORT/health" >/dev/null; then
  echo "Error: /health no responde en http://localhost:$PORT" >&2
  exit 1
fi

ASSET=$(ls demo-ui/dist/assets/*.js 2>/dev/null | head -1 | xargs -n1 basename)
if [ -n "$ASSET" ] && ! curl -sf "http://localhost:$PORT/demo/assets/$ASSET" >/dev/null; then
  echo "Error: assets de demo-ui no disponibles en /demo/assets/" >&2
  exit 1
fi

trap - EXIT INT TERM

echo "==> Demo available at http://localhost:$PORT/demo"
echo "    Refrescá la página (F5) si ya tenías /demo abierto"
echo "    Para detener: Ctrl+C (no uses Ctrl+Z)"
echo "    Press Ctrl+C to stop"

if command -v open &>/dev/null; then
  open "http://localhost:$PORT/demo"
fi

wait $PID

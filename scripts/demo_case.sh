#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://localhost:8000}"

if ! curl -sf "$BASE/health" >/dev/null; then
  echo "Error: API no disponible en $BASE" >&2
  echo "Arrancá el servidor primero, por ejemplo:" >&2
  echo "  ./scripts/record_demo.sh" >&2
  echo "  # o: VIDEO_DEMO=true uvicorn publisher_support.main:app --host 0.0.0.0 --port 8000" >&2
  exit 1
fi

echo "Creating case..."
RESPONSE=$(curl -sf -X POST "$BASE/cases" \
  -H "Content-Type: application/json" \
  -d '{"query":"No puedo publicar","publisher_id":"pub-demo-001","scenario_id":"account_blocked","video_demo":true}')

CASE_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['case_id'])")

echo "Case ID: $CASE_ID"
echo "Polling status..."
for i in $(seq 1 30); do
  STATUS=$(curl -sf "$BASE/cases/$CASE_ID" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "  [$i] status=$STATUS"
  [ "$STATUS" = "resolved" ] && break
  sleep 1
done

curl -sf "$BASE/cases/$CASE_ID" | python3 -m json.tool

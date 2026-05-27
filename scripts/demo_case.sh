#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://localhost:8000}"

echo "Creating case..."
CASE_ID=$(curl -s -X POST "$BASE/cases" \
  -H "Content-Type: application/json" \
  -d '{"query":"No puedo publicar","publisher_id":"pub-demo-001","scenario_id":"account_blocked","video_demo":true}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['case_id'])")

echo "Case ID: $CASE_ID"
echo "Polling status..."
for i in $(seq 1 30); do
  STATUS=$(curl -s "$BASE/cases/$CASE_ID" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "  [$i] status=$STATUS"
  [ "$STATUS" = "resolved" ] && break
  sleep 1
done

curl -s "$BASE/cases/$CASE_ID" | python3 -m json.tool

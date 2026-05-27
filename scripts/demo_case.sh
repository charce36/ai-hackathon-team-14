#!/usr/bin/env bash
# Demo CLI — requiere server corriendo con ANTHROPIC_API_KEY en .env
#
# Uso:
#   ./scripts/demo_case.sh
#   ./scripts/demo_case.sh http://localhost:8000 "No puedo publicar mis avisos"
#   ./scripts/demo_case.sh http://localhost:8000 "Error 503 en la API" gcp_service_down
#
set -euo pipefail

BASE="${1:-http://localhost:8000}"
QUERY="${2:-No puedo publicar mis avisos, me aparece error al intentar publicar}"
SCENARIO_ID="${3:-}"
CASE_FILE=$(mktemp /tmp/case_XXXXXX.json)
trap 'rm -f "$CASE_FILE"' EXIT

echo "==> Health check"
HEALTH=$(curl -s "$BASE/health")
echo "$HEALTH" | python3 -m json.tool

LLM_OK=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('llm_configured', False))")
if [ "$LLM_OK" != "True" ]; then
  echo ""
  echo "ERROR: ANTHROPIC_API_KEY no configurada en el server."
  echo "Copiá .env.example a .env, seteá la key y reiniciá uvicorn."
  exit 1
fi

echo ""
echo "==> Creando caso"
echo "    query: $QUERY"
if [ -n "$SCENARIO_ID" ]; then
  echo "    scenario_id hint: $SCENARIO_ID"
  PAYLOAD=$(QUERY="$QUERY" SCENARIO_ID="$SCENARIO_ID" python3 -c '
import json, os
print(json.dumps({
  "query": os.environ["QUERY"],
  "publisher_id": "pub-demo-001",
  "scenario_id": os.environ["SCENARIO_ID"],
  "video_demo": True,
}))
')
else
  echo "    scenario_id: (Claude decide)"
  PAYLOAD=$(QUERY="$QUERY" python3 -c '
import json, os
print(json.dumps({
  "query": os.environ["QUERY"],
  "publisher_id": "pub-demo-001",
  "video_demo": True,
}))
')
fi

CASE_ID=$(curl -s -X POST "$BASE/cases" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['case_id'])")

echo "    case_id: $CASE_ID"
echo ""
echo "==> Polling..."
for i in $(seq 1 60); do
  curl -s "$BASE/cases/$CASE_ID" > "$CASE_FILE"
  STATUS=$(python3 -c "import json; print(json.load(open('$CASE_FILE'))['status'])")
  echo "  [$i] status=$STATUS"
  if [ "$STATUS" = "resolved" ] || [ "$STATUS" = "escalated" ]; then
    break
  fi
  sleep 1
done

echo ""
echo "==> Resumen (Classifier + RCA via Claude)"
python3 - "$CASE_FILE" <<'PY'
import json, sys
case = json.load(open(sys.argv[1]))

print(f"status: {case['status']}")

if case.get("classified"):
    c = case["classified"]
    print(f"classifier.scenario_id: {c['scenario_id']}")
    print(f"classifier.category: {c['category']} | severity: {c['severity']}")
    print(f"classifier.symptom: {c['symptom']}")

for e in case.get("timeline", []):
    if e["agent"] in ("Classifier", "RCA", "Fix", "System"):
        meta = e.get("metadata") or {}
        reasoning = meta.get("reasoning", "")
        src = meta.get("model_source", "")
        extra = f" [{src}]" if src else ""
        print(f"  [{e['agent']}]{extra} {e['message']}")
        if reasoning:
            tail = "..." if len(reasoning) > 200 else ""
            print(f"    reasoning: {reasoning[:200]}{tail}")

if case.get("root_cause"):
    rc = case["root_cause"]
    print(f"rca.summary: {rc['summary']}")
    print(f"rca.confidence: {rc['confidence']}")

if case.get("proposed_patch"):
    p = case["proposed_patch"]
    print(f"fix.patch_id: {p['patch_id']}")
    print(f"fix.description: {p['description']}")
    files = p.get("files") or []
    if files and files[0].get("content"):
        content = files[0]["content"]
        tail = "..." if len(content) > 400 else ""
        print(f"fix.code_preview:\n{content[:400]}{tail}")

msgs = [m for m in case.get("client_messages", []) if m["type"] != "user"]
print(f"client_messages: {[m['type'] for m in msgs]}")
PY

echo ""
echo "==> JSON completo"
python3 -m json.tool "$CASE_FILE"
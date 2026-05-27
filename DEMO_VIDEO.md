# Guion para grabar el video demo (60–90 segundos)

## Preparación

- Resolución: **1920×1080**, zoom del navegador al **100%**
- URL: `http://localhost:8000/demo`
- Variables: `VIDEO_DEMO=true`, `DEMO_STEP_DELAY_MS=800`

```bash
cd ai-hackathon-team-14
source .venv/bin/activate
pip install -e .
cd demo-ui && npm install && npm run build && cd ..
VIDEO_DEMO=true uvicorn publisher_support.main:app --host 0.0.0.0 --port 8000
```

## Guión T0–T5

| Momento | Acción | WhatsApp (izquierda) | Consola (derecha) |
|---------|--------|----------------------|-------------------|
| T0 | Clic en **"Grabar demo"** o chip *Cuenta bloqueada* | Mensaje del publisher | `[Supervisor] Caso recibido` |
| T1 | ~2 s | *"Estoy verificando tu consulta..."* | `[Classifier] category=account...` |
| T2 | ~5 s | (sin mensaje nuevo) | `[GCP]`, `[MYSQL]`, `[SAP]`, `[ACCOUNT]`, `[RUNDECK]` |
| T3 | ~10 s | *"Identificamos el problema... ~15 min"* | `[RCA]`, `[Fix] patch propuesto` |
| T4 | ~15 s | (sin mensaje) | `[Human]` auto-aprueba → `[CI/CD] job #mock-...` |
| T5 | ~20 s | *"Tu consulta quedó resuelta..."* | `[Verify] tests OK`, `[Notify] caso cerrado` |

## Escenarios alternativos para el video

1. **account_blocked** — más claro para jurado (recomendado)
2. **gcp_service_down** — muestra infra crítica
3. **sap_sync_failure** — billing / SAP

## Tips de grabación

- Pantalla dividida ya integrada: no hace falta OBS con dos fuentes
- Ocultar barra de direcciones del navegador (modo presentación)
- Duración ideal: **60–90 s** por escenario

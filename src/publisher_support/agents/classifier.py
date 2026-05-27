import json
from pathlib import Path

from publisher_support.adapters.scenarios import list_scenarios
from publisher_support.agents.helpers import emit_audit, emit_client_message
from publisher_support.agents.messaging import client_message_checking
from publisher_support.agents.llm_errors import handle_llm_error
from publisher_support.config import ROOT_DIR
from publisher_support.llm.client import invoke_structured
from publisher_support.llm.schemas import ClassifierLLMOutput
from publisher_support.models.schemas import CaseState, CaseStatus, ClassifiedQuery

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _build_catalog() -> str:
    scenarios = list_scenarios()
    lines = []
    for s in scenarios:
        lines.append(f"- id={s.id} | label={s.label} | ejemplo=\"{s.query}\"")
    return "\n".join(lines)


def _build_user_prompt(state: CaseState) -> str:
    hint = ""
    if state.scenario_id:
        hint = f"\nHint del sistema (chip demo): scenario_id sugerido = {state.scenario_id}"
    return (
        f"publisher_id: {state.publisher_id}\n"
        f"consulta del publisher: {state.raw_query}\n"
        f"{hint}\n\n"
        f"Catálogo de escenarios válidos:\n{_build_catalog()}"
    )


async def classify_with_claude(state: CaseState) -> ClassifierLLMOutput:
    return await invoke_structured(
        system=_load_prompt("classifier.md"),
        user=_build_user_prompt(state),
        output_model=ClassifierLLMOutput,
        tool_name="classify_publisher_query",
    )


async def classifier_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.CLASSIFYING

    await emit_client_message(state, client_message_checking())

    try:
        result = await classify_with_claude(state)
    except Exception as exc:
        return await handle_llm_error(state, exc)

    state.scenario_id = result.scenario_id
    state.classified = ClassifiedQuery(
        publisher_id=state.publisher_id,
        portal="ZP",
        symptom=result.symptom_summary,
        category=result.category,
        severity=result.severity,
        affected_services=result.affected_services,
        scenario_id=result.scenario_id,
    )

    await emit_audit(
        state,
        "Classifier",
        (
            f"category={result.category}, severity={result.severity}, "
            f"scenario={result.scenario_id}, services={result.affected_services}"
        ),
        reasoning=result.reasoning,
        model_source="claude",
    )
    return state

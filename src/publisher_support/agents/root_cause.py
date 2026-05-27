import json
from pathlib import Path

from publisher_support.adapters.scenarios import load_scenario
from publisher_support.agents.helpers import emit_audit
from publisher_support.agents.llm_errors import escalate_case, handle_llm_error
from publisher_support.config import settings
from publisher_support.llm.client import invoke_structured
from publisher_support.llm.schemas import RCALLMOutput
from publisher_support.models.schemas import (
    CaseState,
    CaseStatus,
    PatchFile,
    PatchProposal,
    RootCauseReport,
)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _build_rca_user_prompt(state: CaseState) -> str:
    if not state.classified:
        return ""

    scenario = load_scenario(state.classified.scenario_id)
    stacktrace = scenario.get("stacktrace", "No stacktrace disponible")
    monitors = {
        svc: snap.model_dump()
        for svc, snap in state.monitor_results.items()
    }
    timeline = [
        {"agent": e.agent, "message": e.message}
        for e in state.timeline[-8:]
    ]

    return (
        f"Clasificación:\n{state.classified.model_dump_json(indent=2)}\n\n"
        f"Monitor results:\n{json.dumps(monitors, indent=2, ensure_ascii=False)}\n\n"
        f"Stacktrace / logs:\n{stacktrace}\n\n"
        f"Timeline reciente:\n{json.dumps(timeline, indent=2, ensure_ascii=False)}"
    )


async def analyze_with_claude(state: CaseState) -> RCALLMOutput:
    return await invoke_structured(
        system=_load_prompt("rca.md"),
        user=_build_rca_user_prompt(state),
        output_model=RCALLMOutput,
        tool_name="propose_root_cause_and_fix",
        max_tokens=4096,
    )


async def root_cause_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.FIX_PROPOSED
    if not state.classified:
        return await escalate_case(state, "Sin clasificación previa para RCA")

    try:
        result = await analyze_with_claude(state)
    except Exception as exc:
        return await handle_llm_error(state, exc)

    if result.confidence < settings.rca_confidence_threshold:
        return await escalate_case(
            state,
            f"Confianza RCA insuficiente ({result.confidence:.2f} < {settings.rca_confidence_threshold})",
            agent="RCA",
        )

    state.root_cause = RootCauseReport(
        root_cause=result.root_cause,
        confidence=result.confidence,
        eta_minutes=result.eta_minutes,
        summary=result.summary,
    )
    state.proposed_patch = PatchProposal(
        patch_id=result.patch_id,
        description=result.description,
        files=[
            PatchFile(path=f.path, action=f.action, content=f.content)
            for f in result.files
        ],
    )

    code_preview = result.files[0].content[:200] if result.files else ""
    await emit_audit(
        state,
        "RCA",
        f"root_cause={result.summary}, confidence={result.confidence:.2f}",
        reasoning=result.reasoning,
        model_source="claude",
    )
    await emit_audit(
        state,
        "Fix",
        f"patch_id={result.patch_id}: {result.description}",
        files=[f.model_dump() for f in result.files],
        code_preview=code_preview,
        model_source="claude",
    )
    return state

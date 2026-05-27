from typing import TypedDict

from langgraph.graph import END, StateGraph

from publisher_support.agents.classifier import classifier_node
from publisher_support.agents.monitors import monitors_node
from publisher_support.agents.root_cause import root_cause_node
from publisher_support.agents.supervisor import (
    notify_identified_node,
    notify_resolved_node,
    supervisor_node,
)
from publisher_support.agents.verification import verification_node
from publisher_support.cicd.mock_pipeline import mock_cicd_node
from publisher_support.human.approval import human_gate_node
from publisher_support.models.schemas import CaseState, CaseStatus


class WorkflowContext(TypedDict, total=False):
    case: CaseState
    video_demo: bool


async def _wrap(fn, state: WorkflowContext) -> WorkflowContext:
    case = state["case"]
    updated = await fn(case)
    return {"case": updated, "video_demo": state.get("video_demo", True)}


async def _supervisor(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(supervisor_node, state)


async def _classifier(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(classifier_node, state)


async def _monitors(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(monitors_node, state)


async def _root_cause(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(root_cause_node, state)


async def _notify_identified(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(notify_identified_node, state)


async def _human_gate(state: WorkflowContext) -> WorkflowContext:
    case = state["case"]
    updated = await human_gate_node(case, video_demo=state.get("video_demo"))
    return {"case": updated, "video_demo": state.get("video_demo", True)}


async def _mock_cicd(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(mock_cicd_node, state)


async def _verify(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(verification_node, state)


async def _notify_resolved(state: WorkflowContext) -> WorkflowContext:
    return await _wrap(notify_resolved_node, state)


def _route_if_escalated(state: WorkflowContext, next_node: str) -> str:
    if state["case"].status == CaseStatus.ESCALATED:
        return "end"
    return next_node


def _route_after_classifier(state: WorkflowContext) -> str:
    return _route_if_escalated(state, "monitors")


def _route_after_root_cause(state: WorkflowContext) -> str:
    return _route_if_escalated(state, "notify_identified")


def _route_after_human(state: WorkflowContext) -> str:
    case = state["case"]
    if case.status == CaseStatus.ESCALATED:
        return "end"
    return "mock_cicd"


def _route_after_verify(state: WorkflowContext) -> str:
    case = state["case"]
    if case.verification and case.verification.resolved:
        return "notify_resolved"
    return "end"


def build_workflow() -> StateGraph:
    graph = StateGraph(WorkflowContext)
    graph.add_node("supervisor", _supervisor)
    graph.add_node("classifier", _classifier)
    graph.add_node("monitors", _monitors)
    graph.add_node("root_cause", _root_cause)
    graph.add_node("notify_identified", _notify_identified)
    graph.add_node("human_gate", _human_gate)
    graph.add_node("mock_cicd", _mock_cicd)
    graph.add_node("verify", _verify)
    graph.add_node("notify_resolved", _notify_resolved)

    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "classifier")
    graph.add_conditional_edges(
        "classifier",
        _route_after_classifier,
        {"monitors": "monitors", "end": END},
    )
    graph.add_edge("monitors", "root_cause")
    graph.add_conditional_edges(
        "root_cause",
        _route_after_root_cause,
        {"notify_identified": "notify_identified", "end": END},
    )
    graph.add_edge("notify_identified", "human_gate")
    graph.add_conditional_edges("human_gate", _route_after_human, {"mock_cicd": "mock_cicd", "end": END})
    graph.add_edge("mock_cicd", "verify")
    graph.add_conditional_edges("verify", _route_after_verify, {"notify_resolved": "notify_resolved", "end": END})
    graph.add_edge("notify_resolved", END)
    return graph


async def run_case(case: CaseState, video_demo: bool | None = None) -> CaseState:
    workflow = build_workflow().compile()
    result = await workflow.ainvoke(
        {"case": case, "video_demo": video_demo if video_demo is not None else True}
    )
    return result["case"]

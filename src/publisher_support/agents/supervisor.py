from publisher_support.adapters.scenarios import detect_scenario, load_scenario
from publisher_support.agents.helpers import emit_audit, emit_client_message
from publisher_support.models.events import ClientMessage, ClientMessageType
from publisher_support.models.schemas import CaseState, CaseStatus, ClassifiedQuery


CATEGORY_MAP = {
    "account_blocked": ("account", "high"),
    "sap_sync_failure": ("billing", "medium"),
    "mysql_replication_lag": ("data_sync", "medium"),
    "gcp_service_down": ("infrastructure", "critical"),
    "rundeck_job_failed": ("batch", "medium"),
}

SERVICE_MAP = {
    "account_blocked": ["account"],
    "sap_sync_failure": ["sap"],
    "mysql_replication_lag": ["mysql"],
    "gcp_service_down": ["gcp"],
    "rundeck_job_failed": ["rundeck"],
}


async def supervisor_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.RECEIVED
    await emit_audit(
        state,
        "Supervisor",
        f"Caso #{state.case_id} recibido de publisher {state.publisher_id}",
        query=state.raw_query[:80],
    )
    return state


async def classifier_node(state: CaseState) -> CaseState:
    state.status = CaseStatus.CLASSIFYING
    scenario_id = detect_scenario(state.raw_query, state.scenario_id)
    state.scenario_id = scenario_id
    category, severity = CATEGORY_MAP.get(scenario_id, ("general", "medium"))
    affected = SERVICE_MAP.get(scenario_id, ["account"])

    state.classified = ClassifiedQuery(
        publisher_id=state.publisher_id,
        portal="ZP",
        symptom=state.raw_query,
        category=category,
        severity=severity,
        affected_services=affected,
        scenario_id=scenario_id,
    )

    await emit_client_message(
        state,
        ClientMessage(
            type=ClientMessageType.CHECKING,
            text="Estoy verificando tu consulta, aguardá un momento.",
        ),
    )
    await emit_audit(
        state,
        "Classifier",
        f"category={category}, severity={severity}, scenario={scenario_id}, services={affected}",
    )
    return state


async def notify_identified_node(state: CaseState) -> CaseState:
    if not state.root_cause:
        return state
    await emit_client_message(
        state,
        ClientMessage(
            type=ClientMessageType.IDENTIFIED,
            text=(
                f"Identificamos el problema: {state.root_cause.summary}. "
                f"Lo resolveremos en aproximadamente {state.root_cause.eta_minutes} minutos."
            ),
        ),
    )
    await emit_audit(state, "Notify", "Mensaje de progreso enviado al publisher")
    return state


async def notify_resolved_node(state: CaseState) -> CaseState:
    scenario_id = (
        state.classified.scenario_id
        if state.classified
        else state.scenario_id or "account_blocked"
    )
    scenario = load_scenario(scenario_id)
    resolution = scenario.get("resolution", {}).get("summary")
    if not resolution and state.root_cause:
        resolution = state.root_cause.summary
    if not resolution:
        resolution = "tu consulta"

    await emit_client_message(
        state,
        ClientMessage(
            type=ClientMessageType.RESOLVED,
            text=f"Tu consulta quedó resuelta: {resolution}. Ya podés operar con normalidad.",
        ),
    )
    state.status = CaseStatus.RESOLVED
    await emit_audit(state, "Notify", "Caso cerrado — publisher notificado")
    return state

export interface Scenario {
  id: string;
  label: string;
  query: string;
  publisher_id: string;
}

export interface ClientMessage {
  id: string;
  type: "checking" | "identified" | "resolved" | "user";
  text: string;
  timestamp: string;
}

export interface AuditEvent {
  id: string;
  agent: string;
  message: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

function agentClass(agent: string): string {
  const key = agent.toLowerCase().replace(/\//g, "\\/");
  return `agent-${key}`;
}

export function formatConsoleLine(event: AuditEvent): { className: string; text: string } {
  const time = new Date(event.timestamp).toLocaleTimeString("es-AR", { hour12: false });
  return {
    className: agentClass(event.agent),
    text: `[${time}] [${event.agent}] ${event.message}`,
  };
}

export async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch("/scenarios");
  return res.json();
}

export async function createCase(query: string, publisherId: string, scenarioId?: string): Promise<string> {
  const res = await fetch("/cases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      publisher_id: publisherId,
      scenario_id: scenarioId,
      video_demo: true,
    }),
  });
  const data = await res.json();
  return data.case_id;
}

export function subscribeCaseEvents(
  caseId: string,
  onClientMessage: (msg: ClientMessage) => void,
  onAudit: (event: AuditEvent) => void,
): () => void {
  const source = new EventSource(`/cases/${caseId}/events`);

  source.addEventListener("client_message", (e) => {
    const data = JSON.parse(e.data) as ClientMessage;
    if (data.type !== "user") {
      onClientMessage(data);
    }
  });

  source.addEventListener("audit", (e) => {
    onAudit(JSON.parse(e.data) as AuditEvent);
  });

  return () => source.close();
}

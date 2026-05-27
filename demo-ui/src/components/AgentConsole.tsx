import { AuditEvent, formatConsoleLine } from "../api";

interface Props {
  events: AuditEvent[];
  caseId: string | null;
  running: boolean;
}

export default function AgentConsole({ events, caseId, running }: Props) {
  return (
    <div className="demo-console-panel">
      <div className="status-bar">
        {caseId ? `Caso #${caseId}` : "Sin caso activo"}
        {running ? " · procesando..." : ""}
      </div>
      {events.map((event) => {
        const line = formatConsoleLine(event);
        return (
          <div key={event.id} className={`console-line ${line.className}`}>
            {line.text}
          </div>
        );
      })}
      {events.length === 0 && (
        <div className="console-line" style={{ color: "#8b949e" }}>
          La consola mostrará los pasos de cada agente en tiempo real...
        </div>
      )}
    </div>
  );
}

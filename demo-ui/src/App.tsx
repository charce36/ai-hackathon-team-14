import { useCallback, useEffect, useRef, useState } from "react";
import {
  AuditEvent,
  ClientMessage,
  Scenario,
  createCase,
  fetchScenarios,
  subscribeCaseEvents,
} from "./api";
import AgentConsole from "./components/AgentConsole";
import InboxView from "./components/InboxView";
import PhoneFrame from "./components/PhoneFrame";
import ScenarioChips from "./components/ScenarioChips";
import WhatsAppChat from "./components/WhatsAppChat";

function userMessage(text: string): ClientMessage {
  return {
    id: crypto.randomUUID(),
    type: "user",
    text,
    timestamp: new Date().toISOString(),
  };
}

export default function App() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [messages, setMessages] = useState<ClientMessage[]>([]);
  const [consoleEvents, setConsoleEvents] = useState<AuditEvent[]>([]);
  const [input, setInput] = useState("");
  const [caseId, setCaseId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchScenarios().then(setScenarios).catch(console.error);
  }, []);

  useEffect(() => {
    return () => unsubscribeRef.current?.();
  }, []);

  const startCase = useCallback(async (query: string, publisherId: string, scenarioId?: string) => {
    unsubscribeRef.current?.();
    setRunning(true);
    setConsoleEvents([]);
    setMessages([userMessage(query)]);

    try {
      const id = await createCase(query, publisherId, scenarioId);
      setCaseId(id);
      unsubscribeRef.current = subscribeCaseEvents(
        id,
        (msg) => setMessages((prev) => [...prev, msg]),
        (event) => setConsoleEvents((prev) => [...prev, event]),
      );
    } catch (err) {
      console.error(err);
    } finally {
      setTimeout(() => setRunning(false), 15000);
    }
  }, []);

  const handleSend = () => {
    if (!input.trim() || running) return;
    startCase(input.trim(), "pub-demo-001");
    setInput("");
  };

  const handleScenario = (scenario: Scenario) => {
    if (running) return;
    startCase(scenario.query, scenario.publisher_id, scenario.id);
  };

  const handleRecordDemo = () => {
    const demo = scenarios.find((s) => s.id === "account_blocked") ?? scenarios[0];
    if (demo) handleScenario(demo);
  };

  const [view, setView] = useState<"demo" | "inbox">("demo");

  if (view === "inbox") {
    return (
      <div style={{ position: "relative" }}>
        <button onClick={() => setView("demo")}
          style={{ position: "fixed", top: 10, right: 16, zIndex: 999,
            padding: "5px 12px", borderRadius: 8, border: "none",
            background: "#334155", color: "#fff", fontSize: 12, fontWeight: 600,
            cursor: "pointer", fontFamily: "inherit" }}>
          ← Demo original
        </button>
        <InboxView scenarios={scenarios} />
      </div>
    );
  }

  return (
    <div className="demo-shell">
      <header className="demo-header" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 16, position: "relative" }}>
        Publisher Support Agent — Demo QuintoAndar
        <button onClick={() => setView("inbox")}
          style={{ position: "absolute", right: 12,
            padding: "4px 12px", borderRadius: 8, border: "none",
            background: "#6366f1", color: "#fff", fontSize: 12, fontWeight: 600,
            cursor: "pointer", fontFamily: "inherit" }}>
          Inbox →
        </button>
      </header>
      <div className="demo-phone-panel">
        <PhoneFrame>
          <WhatsAppChat
            messages={messages}
            input={input}
            onInputChange={setInput}
            onSend={handleSend}
            disabled={running}
          />
          <div style={{
            background: "#efeae2", padding: "8px 10px 10px",
            display: "flex", flexDirection: "column", gap: 7, flexShrink: 0,
            borderTop: "1px solid rgba(0,0,0,0.06)",
          }}>
            <ScenarioChips scenarios={scenarios} onSelect={handleScenario} disabled={running} />
            <button onClick={handleRecordDemo} disabled={running} style={{
              width: "100%", padding: "9px 0", borderRadius: 12, border: "none",
              background: running
                ? "rgba(7,94,84,0.45)"
                : "linear-gradient(135deg, #25d366, #075e54)",
              color: "#fff", fontSize: 13, fontWeight: 700, cursor: running ? "not-allowed" : "pointer",
              letterSpacing: "0.02em", boxShadow: running ? "none" : "0 2px 8px rgba(7,94,84,0.35)",
              transition: "all 0.2s", fontFamily: "inherit",
            }}>
              {running ? "Procesando…" : "▶  Grabar demo (cuenta bloqueada)"}
            </button>
          </div>
        </PhoneFrame>
      </div>
      <AgentConsole events={consoleEvents} caseId={caseId} running={running} />
    </div>
  );
}

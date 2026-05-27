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

  return (
    <div className="demo-shell">
      <header className="demo-header">Publisher Support Agent — Demo QuintoAndar</header>
      <div className="demo-phone-panel">
        <PhoneFrame>
          <WhatsAppChat
            messages={messages}
            input={input}
            onInputChange={setInput}
            onSend={handleSend}
            disabled={running}
          />
          <div className="wa-input-area" style={{ background: "#ece5dd" }}>
            <ScenarioChips scenarios={scenarios} onSelect={handleScenario} disabled={running} />
            <button className="record-btn" onClick={handleRecordDemo} disabled={running}>
              Grabar demo (cuenta bloqueada)
            </button>
          </div>
        </PhoneFrame>
      </div>
      <AgentConsole events={consoleEvents} caseId={caseId} running={running} />
    </div>
  );
}

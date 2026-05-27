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
import InboxView, { Conversation } from "./components/InboxView";
import PhoneFrame from "./components/PhoneFrame";
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
  const [liveConversations, setLiveConversations] = useState<Conversation[]>([]);
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
    const firstMsg = userMessage(query);
    setMessages([firstMsg]);

    try {
      const id = await createCase(query, publisherId, scenarioId);
      setCaseId(id);

      const now = new Date().toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false });
      const newConv: Conversation = {
        id,
        publisherId,
        scenarioId: scenarioId ?? "",
        lastMessage: query,
        timestamp: now,
        status: "in_progress",
        unread: true,
        messages: [firstMsg],
        events: [],
      };
      setLiveConversations(prev => [newConv, ...prev]);

      unsubscribeRef.current = subscribeCaseEvents(
        id,
        (msg) => {
          setMessages((prev) => [...prev, msg]);
          setLiveConversations(prev => prev.map(c =>
            c.id === id
              ? { ...c, messages: [...c.messages, msg], lastMessage: msg.text,
                  status: msg.type === "resolved" ? "resolved" : "in_progress" }
              : c
          ));
        },
        (event) => {
          setConsoleEvents((prev) => [...prev, event]);
          setLiveConversations(prev => prev.map(c =>
            c.id === id ? { ...c, events: [...c.events, event] } : c
          ));
        },
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
        <InboxView scenarios={scenarios} liveConversations={liveConversations} />
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
        </PhoneFrame>
      </div>
      <AgentConsole events={consoleEvents} caseId={caseId} running={running} />
    </div>
  );
}

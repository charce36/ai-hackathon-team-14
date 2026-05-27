import { useCallback, useEffect, useRef, useState } from "react";
import {
  AuditEvent,
  ClientMessage,
  Scenario,
  createCase,
  subscribeCaseEvents,
} from "../api";

// ─── Mock publisher data ──────────────────────────────────────────────────────

interface Publisher {
  id: string;
  name: string;
  email: string;
  company: string;
  plan: "Starter" | "Professional" | "Premium";
  accountStatus: "active" | "blocked" | "suspended";
  listings: number;
  activeListings: number;
  joinedDate: string;
  avatarColor: string;
  phone: string;
}

interface Conversation {
  id: string;
  publisherId: string;
  scenarioId: string;
  lastMessage: string;
  timestamp: string;
  status: "open" | "in_progress" | "resolved";
  unread: boolean;
  messages: ClientMessage[];
  events: AuditEvent[];
}

const PUBLISHERS: Record<string, Publisher> = {
  "pub-001": {
    id: "pub-001", name: "Inmobiliaria Del Plata", email: "ops@delplata.com.ar",
    company: "Del Plata S.R.L.", plan: "Premium", accountStatus: "blocked",
    listings: 48, activeListings: 0, joinedDate: "2021-03-15",
    avatarColor: "#6366f1", phone: "+54 11 4521-8800",
  },
  "pub-002": {
    id: "pub-002", name: "Propiedades Sudeste", email: "admin@sudeste.com",
    company: "Sudeste Inmuebles S.A.", plan: "Professional", accountStatus: "active",
    listings: 124, activeListings: 98, joinedDate: "2019-07-22",
    avatarColor: "#0ea5e9", phone: "+54 11 5034-2200",
  },
  "pub-003": {
    id: "pub-003", name: "Estudio Bianchi & Asoc.", email: "facturacion@bianchi.ar",
    company: "Bianchi & Asociados", plan: "Starter", accountStatus: "active",
    listings: 17, activeListings: 12, joinedDate: "2023-01-10",
    avatarColor: "#f59e0b", phone: "+54 351 422-9100",
  },
  "pub-004": {
    id: "pub-004", name: "Desarrollos Norte S.A.", email: "sistemas@dnorte.com",
    company: "Desarrollos Norte S.A.", plan: "Premium", accountStatus: "active",
    listings: 312, activeListings: 287, joinedDate: "2018-11-05",
    avatarColor: "#10b981", phone: "+54 11 4800-5500",
  },
  "pub-005": {
    id: "pub-005", name: "Alquileres Rápidos", email: "soporte@alqrapidos.com",
    company: "AR Digital S.R.L.", plan: "Professional", accountStatus: "suspended",
    listings: 33, activeListings: 0, joinedDate: "2022-05-18",
    avatarColor: "#ef4444", phone: "+54 11 6120-4400",
  },
};

const MOCK_CONVERSATIONS: Conversation[] = [
  { id: "case-1", publisherId: "pub-001", scenarioId: "account_blocked",
    lastMessage: "No puedo publicar nuevas propiedades, me dice cuenta bloqueada",
    timestamp: "10:42", status: "in_progress", unread: true, messages: [], events: [] },
  { id: "case-2", publisherId: "pub-002", scenarioId: "mysql_replication_lag",
    lastMessage: "El panel tarda mucho en actualizar los datos de mis avisos",
    timestamp: "09:15", status: "open", unread: true, messages: [], events: [] },
  { id: "case-3", publisherId: "pub-003", scenarioId: "sap_sync_failure",
    lastMessage: "La facturación no coincide con lo que me llega por email",
    timestamp: "Ayer", status: "open", unread: false, messages: [], events: [] },
  { id: "case-4", publisherId: "pub-004", scenarioId: "gcp_service_down",
    lastMessage: "Las fotos de varios avisos no cargan desde esta mañana",
    timestamp: "Ayer", status: "resolved", unread: false, messages: [], events: [] },
  { id: "case-5", publisherId: "pub-005", scenarioId: "rundeck_job_failed",
    lastMessage: "El proceso batch de sincronización falló esta madrugada",
    timestamp: "Lun", status: "resolved", unread: false, messages: [], events: [] },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function initials(name: string) {
  return name.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase();
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: Conversation["status"] }) {
  const map = {
    open:        { label: "Abierto",      bg: "#fef9c3", color: "#854d0e" },
    in_progress: { label: "En progreso",  bg: "#dbeafe", color: "#1e40af" },
    resolved:    { label: "Resuelto",     bg: "#dcfce7", color: "#166534" },
  };
  const s = map[status];
  return (
    <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.04em",
      padding: "2px 7px", borderRadius: 99, background: s.bg, color: s.color }}>
      {s.label.toUpperCase()}
    </span>
  );
}

function AccountStatusDot({ status }: { status: Publisher["accountStatus"] }) {
  const map = { active: "#22c55e", blocked: "#ef4444", suspended: "#f59e0b" };
  const label = { active: "Activa", blocked: "Bloqueada", suspended: "Suspendida" };
  return (
    <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <span style={{ width: 8, height: 8, borderRadius: "50%",
        background: map[status], boxShadow: `0 0 0 2px ${map[status]}33` }} />
      <span style={{ fontSize: 13, color: map[status], fontWeight: 600 }}>
        {label[status]}
      </span>
    </span>
  );
}

function Avatar({ name, color, size = 36 }: { name: string; color: string; size?: number }) {
  return (
    <div style={{ width: size, height: size, borderRadius: "50%", background: color,
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "#fff", fontWeight: 700, fontSize: size * 0.38, flexShrink: 0,
      letterSpacing: "0.01em" }}>
      {initials(name)}
    </div>
  );
}

// ─── Chat panel ───────────────────────────────────────────────────────────────

function ChatPanel({ conv, scenarios, onNewCase }: {
  conv: Conversation;
  scenarios: Scenario[];
  onNewCase: (msgs: ClientMessage[], events: AuditEvent[]) => void;
}) {
  const pub = PUBLISHERS[conv.publisherId];
  const scenario = scenarios.find(s => s.id === conv.scenarioId);
  const [messages, setMessages] = useState<ClientMessage[]>(conv.messages);
  const [events, setEvents] = useState<AuditEvent[]>(conv.events);
  const [running, setRunning] = useState(false);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startCase = useCallback(async () => {
    if (running || !scenario) return;
    setRunning(true);
    const userMsg: ClientMessage = {
      id: crypto.randomUUID(), type: "user",
      text: conv.lastMessage, timestamp: new Date().toISOString(),
    };
    setMessages([userMsg]);
    setEvents([]);
    try {
      const id = await createCase(conv.lastMessage, conv.publisherId, scenario.id);
      const unsub = subscribeCaseEvents(
        id,
        (msg) => setMessages(prev => [...prev, msg]),
        (evt) => setEvents(prev => [...prev, evt]),
      );
      setTimeout(() => { unsub(); setRunning(false); }, 20000);
    } catch { setRunning(false); }
  }, [conv, scenario, running]);

  const handleSend = () => {
    if (!input.trim() || running) return;
    const userMsg: ClientMessage = {
      id: crypto.randomUUID(), type: "user",
      text: input.trim(), timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
  };

  const bubbleStyle = (type: ClientMessage["type"]): React.CSSProperties => {
    const isUser = type === "user";
    return {
      maxWidth: "72%", padding: "9px 14px", borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
      background: isUser ? "#6366f1" : "#f1f5f9",
      color: isUser ? "#fff" : "#1e293b",
      fontSize: 14, lineHeight: 1.5,
      boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
      alignSelf: isUser ? "flex-end" : "flex-start",
    };
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#f8fafc" }}>
      {/* Chat header */}
      <div style={{ padding: "14px 20px", background: "#fff", borderBottom: "1px solid #e2e8f0",
        display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Avatar name={pub.name} color={pub.avatarColor} size={36} />
          <div>
            <div style={{ fontWeight: 600, fontSize: 14, color: "#0f172a" }}>{pub.name}</div>
            <div style={{ fontSize: 12, color: "#64748b" }}>{conv.lastMessage.slice(0, 45)}…</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <StatusBadge status={conv.status} />
          {messages.length === 0 && (
            <button onClick={startCase} disabled={running || !scenario}
              style={{ padding: "6px 14px", borderRadius: 8, border: "none",
                background: "#6366f1", color: "#fff", fontSize: 12, fontWeight: 600,
                cursor: "pointer", opacity: running ? 0.6 : 1, transition: "opacity 0.15s" }}>
              {running ? "Procesando…" : "Simular caso"}
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px",
        display: "flex", flexDirection: "column", gap: 8 }}>
        {messages.length === 0 ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center",
            justifyContent: "center", height: "100%", gap: 12, color: "#94a3b8" }}>
            <div style={{ fontSize: 36 }}>💬</div>
            <div style={{ fontSize: 14, fontWeight: 500 }}>Sin mensajes aún</div>
            <div style={{ fontSize: 13 }}>Hacé clic en "Simular caso" para iniciar</div>
          </div>
        ) : messages.map(msg => (
          <div key={msg.id} style={{ display: "flex",
            justifyContent: msg.type === "user" ? "flex-end" : "flex-start" }}>
            <div style={bubbleStyle(msg.type)}>
              {msg.text}
              <div style={{ fontSize: 10, marginTop: 4, opacity: 0.6, textAlign: "right" }}>
                {new Date(msg.timestamp).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false })}
              </div>
            </div>
          </div>
        ))}
        {running && (
          <div style={{ alignSelf: "flex-start", display: "flex", gap: 5, padding: "10px 14px",
            background: "#f1f5f9", borderRadius: "16px 16px 16px 4px" }}>
            {[0, 1, 2].map(i => (
              <span key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: "#94a3b8",
                animation: "bounce 1.2s ease-in-out infinite",
                animationDelay: `${i * 0.2}s` }} />
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "12px 16px", background: "#fff", borderTop: "1px solid #e2e8f0",
        display: "flex", gap: 10, alignItems: "flex-end", flexShrink: 0 }}>
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSend()}
          placeholder="Escribir respuesta…"
          style={{ flex: 1, padding: "10px 14px", borderRadius: 10,
            border: "1px solid #e2e8f0", fontSize: 14, outline: "none",
            background: "#f8fafc", color: "#0f172a",
            transition: "border-color 0.15s", fontFamily: "inherit" }} />
        <button onClick={handleSend} disabled={!input.trim()}
          style={{ width: 38, height: 38, borderRadius: 10, border: "none",
            background: input.trim() ? "#6366f1" : "#e2e8f0",
            color: input.trim() ? "#fff" : "#94a3b8",
            display: "flex", alignItems: "center", justifyContent: "center",
            cursor: input.trim() ? "pointer" : "default", transition: "all 0.15s", flexShrink: 0 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}

// ─── Publisher sidebar ────────────────────────────────────────────────────────

function PublisherSidebar({ publisherId }: { publisherId: string }) {
  const pub = PUBLISHERS[publisherId];

  const planColor = { Starter: "#64748b", Professional: "#0ea5e9", Premium: "#6366f1" };

  const InfoRow = ({ label, value }: { label: string; value: string }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "8px 0", borderBottom: "1px solid #f1f5f9" }}>
      <span style={{ fontSize: 12, color: "#64748b", fontWeight: 500 }}>{label}</span>
      <span style={{ fontSize: 13, color: "#1e293b", fontWeight: 500 }}>{value}</span>
    </div>
  );

  const StatCard = ({ label, value, sub }: { label: string; value: number | string; sub?: string }) => (
    <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 14px",
      border: "1px solid #e2e8f0", flex: 1 }}>
      <div style={{ fontSize: 22, fontWeight: 700, color: "#0f172a", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 11, color: "#64748b", marginTop: 4, fontWeight: 500 }}>{label}</div>
      {sub && <div style={{ fontSize: 10, color: "#94a3b8", marginTop: 2 }}>{sub}</div>}
    </div>
  );

  return (
    <div style={{ width: 272, borderLeft: "1px solid #e2e8f0", background: "#fff",
      overflowY: "auto", flexShrink: 0, display: "flex", flexDirection: "column" }}>

      {/* Header */}
      <div style={{ padding: "20px 20px 16px", borderBottom: "1px solid #e2e8f0" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
          <Avatar name={pub.name} color={pub.avatarColor} size={52} />
          <div style={{ textAlign: "center" }}>
            <div style={{ fontWeight: 700, fontSize: 15, color: "#0f172a" }}>{pub.name}</div>
            <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{pub.email}</div>
          </div>
          <AccountStatusDot status={pub.accountStatus} />
        </div>
      </div>

      {/* Stats */}
      <div style={{ padding: "14px 16px", borderBottom: "1px solid #e2e8f0" }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: "#94a3b8", letterSpacing: "0.08em",
          marginBottom: 10, textTransform: "uppercase" }}>Publicaciones</div>
        <div style={{ display: "flex", gap: 8 }}>
          <StatCard label="Total" value={pub.listings} />
          <StatCard label="Activas" value={pub.activeListings}
            sub={`${Math.round((pub.activeListings / Math.max(pub.listings, 1)) * 100)}% del total`} />
        </div>
      </div>

      {/* Account info */}
      <div style={{ padding: "14px 16px", borderBottom: "1px solid #e2e8f0" }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: "#94a3b8", letterSpacing: "0.08em",
          marginBottom: 4, textTransform: "uppercase" }}>Cuenta</div>
        <InfoRow label="ID Publisher" value={pub.id} />
        <InfoRow label="Empresa" value={pub.company} />
        <InfoRow label="Teléfono" value={pub.phone} />
        <InfoRow label="Miembro desde" value={new Date(pub.joinedDate).toLocaleDateString("es-AR", { month: "short", year: "numeric" })} />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 8 }}>
          <span style={{ fontSize: 12, color: "#64748b", fontWeight: 500 }}>Plan</span>
          <span style={{ fontSize: 12, fontWeight: 700, padding: "3px 10px", borderRadius: 99,
            background: `${planColor[pub.plan]}18`, color: planColor[pub.plan] }}>
            {pub.plan}
          </span>
        </div>
      </div>

      {/* Quick actions */}
      <div style={{ padding: "14px 16px" }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: "#94a3b8", letterSpacing: "0.08em",
          marginBottom: 10, textTransform: "uppercase" }}>Acciones rápidas</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {[
            { label: "Ver perfil completo", icon: "👤" },
            { label: "Historial de casos",  icon: "📋" },
            { label: "Enviar notificación", icon: "🔔" },
          ].map(action => (
            <button key={action.label}
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px",
                borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff",
                color: "#475569", fontSize: 13, fontWeight: 500, cursor: "pointer",
                textAlign: "left", transition: "all 0.15s", fontFamily: "inherit" }}
              onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = "#f8fafc"; (e.currentTarget as HTMLButtonElement).style.borderColor = "#cbd5e1"; }}
              onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = "#fff"; (e.currentTarget as HTMLButtonElement).style.borderColor = "#e2e8f0"; }}>
              <span>{action.icon}</span> {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Main InboxView ───────────────────────────────────────────────────────────

export default function InboxView({ scenarios }: { scenarios: Scenario[] }) {
  const [conversations] = useState<Conversation[]>(MOCK_CONVERSATIONS);
  const [selectedId, setSelectedId] = useState<string>(MOCK_CONVERSATIONS[0].id);
  const [filter, setFilter] = useState<"all" | "open" | "in_progress" | "resolved">("all");

  const filtered = conversations.filter(c => filter === "all" || c.status === filter);
  const selected = conversations.find(c => c.id === selectedId)!;

  const counts = {
    all: conversations.length,
    open: conversations.filter(c => c.status === "open").length,
    in_progress: conversations.filter(c => c.status === "in_progress").length,
    resolved: conversations.filter(c => c.status === "resolved").length,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh",
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      background: "#fff" }}>

      {/* Top bar */}
      <div style={{ height: 52, background: "#0f172a", display: "flex", alignItems: "center",
        justifyContent: "space-between", padding: "0 20px", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: "#6366f1",
            display: "flex", alignItems: "center", justifyContent: "center" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <span style={{ color: "#fff", fontWeight: 700, fontSize: 14 }}>Publisher Support</span>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "#94a3b8" }}>
            {counts.open + counts.in_progress} conversaciones activas
          </span>
          <button style={{ padding: "6px 14px", borderRadius: 8, border: "none",
            background: "#6366f1", color: "#fff", fontSize: 12, fontWeight: 600, cursor: "pointer" }}>
            + Nuevo caso
          </button>
        </div>
      </div>

      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

        {/* Left sidebar — conversation list */}
        <div style={{ width: 300, borderRight: "1px solid #e2e8f0", display: "flex",
          flexDirection: "column", background: "#fff", flexShrink: 0 }}>

          {/* Search */}
          <div style={{ padding: "12px 14px", borderBottom: "1px solid #f1f5f9" }}>
            <div style={{ position: "relative" }}>
              <svg style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)",
                color: "#94a3b8", pointerEvents: "none" }}
                width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input placeholder="Buscar conversación…"
                style={{ width: "100%", padding: "7px 10px 7px 32px", borderRadius: 8,
                  border: "1px solid #e2e8f0", fontSize: 13, outline: "none",
                  background: "#f8fafc", color: "#0f172a", boxSizing: "border-box",
                  fontFamily: "inherit" }} />
            </div>
          </div>

          {/* Filters */}
          <div style={{ display: "flex", padding: "8px 10px", gap: 4,
            borderBottom: "1px solid #f1f5f9", flexShrink: 0 }}>
            {(["all", "open", "in_progress", "resolved"] as const).map(f => {
              const labels = { all: "Todos", open: "Abiertos", in_progress: "En progreso", resolved: "Resueltos" };
              const active = filter === f;
              return (
                <button key={f} onClick={() => setFilter(f)}
                  style={{ flex: 1, padding: "5px 4px", borderRadius: 7, border: "none",
                    background: active ? "#6366f1" : "transparent",
                    color: active ? "#fff" : "#64748b",
                    fontSize: 11, fontWeight: 600, cursor: "pointer",
                    transition: "all 0.15s", fontFamily: "inherit" }}>
                  {labels[f]}
                  <span style={{ marginLeft: 4, fontSize: 10,
                    opacity: active ? 0.8 : 0.6 }}>({counts[f]})</span>
                </button>
              );
            })}
          </div>

          {/* Conversation list */}
          <div style={{ flex: 1, overflowY: "auto" }}>
            {filtered.map(conv => {
              const pub = PUBLISHERS[conv.publisherId];
              const isSelected = conv.id === selectedId;
              return (
                <div key={conv.id} onClick={() => setSelectedId(conv.id)}
                  style={{ padding: "12px 14px", cursor: "pointer", borderBottom: "1px solid #f8fafc",
                    background: isSelected ? "#eef2ff" : "transparent",
                    borderLeft: `3px solid ${isSelected ? "#6366f1" : "transparent"}`,
                    transition: "background 0.1s" }}
                  onMouseEnter={e => { if (!isSelected) (e.currentTarget as HTMLDivElement).style.background = "#f8fafc"; }}
                  onMouseLeave={e => { if (!isSelected) (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <div style={{ position: "relative", flexShrink: 0 }}>
                      <Avatar name={pub.name} color={pub.avatarColor} size={38} />
                      {conv.unread && (
                        <span style={{ position: "absolute", top: -2, right: -2,
                          width: 10, height: 10, borderRadius: "50%",
                          background: "#6366f1", border: "2px solid #fff" }} />
                      )}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", justifyContent: "space-between",
                        alignItems: "center", marginBottom: 2 }}>
                        <span style={{ fontWeight: conv.unread ? 700 : 500, fontSize: 13,
                          color: "#0f172a", whiteSpace: "nowrap", overflow: "hidden",
                          textOverflow: "ellipsis", maxWidth: 140 }}>
                          {pub.name}
                        </span>
                        <span style={{ fontSize: 11, color: "#94a3b8", flexShrink: 0 }}>
                          {conv.timestamp}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: "#64748b", whiteSpace: "nowrap",
                        overflow: "hidden", textOverflow: "ellipsis", marginBottom: 5 }}>
                        {conv.lastMessage}
                      </div>
                      <StatusBadge status={conv.status} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center — chat */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <ChatPanel conv={selected} scenarios={scenarios} onNewCase={() => {}} />
        </div>

        {/* Right — publisher info */}
        <PublisherSidebar publisherId={selected.publisherId} />
      </div>

      {/* Bounce animation */}
      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  );
}

import { useEffect, useRef } from "react";
import { ClientMessage } from "../api";

interface Props {
  messages: ClientMessage[];
  input: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false });
}

const WA_GREEN       = "#075e54";
const WA_GREEN_LIGHT = "#128c7e";
const WA_BUBBLE_OUT  = "#d9fdd3";
const WA_BG          = "#efeae2";

export default function WhatsAppChat({ messages, input, onInputChange, onSend, disabled }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, disabled]);

  const hasText = input.trim().length > 0;

  return (
    <>
      {/* ── Header ─────────────────────────────────────────────── */}
      <div style={{
        background: WA_GREEN, color: "#fff", padding: "10px 14px",
        display: "flex", alignItems: "center", gap: 10,
        boxShadow: "0 1px 3px rgba(0,0,0,0.25)", flexShrink: 0,
      }}>
        {/* Back arrow */}
        <svg width="10" height="16" viewBox="0 0 10 16" fill="none" style={{ opacity: 0.9 }}>
          <path d="M9 1L1 8l8 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>

        {/* Avatar — QuintoAndar logo */}
        <div style={{
          width: 38, height: 38, borderRadius: "50%", flexShrink: 0,
          background: "#fff",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)", overflow: "hidden", padding: 6,
        }}>
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: "100%", height: "100%" }}>
            <path fillRule="evenodd" clipRule="evenodd" d="M0 24.01V0h24.103v24.01h-3.579v-.001l-.001.001-8.593-8.56 2.547-2.536 6.047 6.024V3.564H3.59v16.858h7.322v3.588H0Z" fill="#3957BD"/>
          </svg>
        </div>

        {/* Name + status */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 15, lineHeight: 1.2, letterSpacing: "0.01em" }}>
            Soporte QuintoAndar
          </div>
          <div style={{ fontSize: 12, opacity: 0.85, display: "flex", alignItems: "center", gap: 4 }}>
            {disabled ? (
              <>
                <span>escribiendo</span>
                <TypingDots />
              </>
            ) : (
              <span>en línea</span>
            )}
          </div>
        </div>

        {/* Icons */}
        <div style={{ display: "flex", gap: 18, opacity: 0.9 }}>
          {/* Video call */}
          <svg width="22" height="16" viewBox="0 0 22 16" fill="none">
            <rect x="1" y="1" width="13" height="14" rx="2" stroke="white" strokeWidth="1.8"/>
            <path d="M14 5.5l7-3.5v12l-7-3.5" stroke="white" strokeWidth="1.8" strokeLinejoin="round"/>
          </svg>
          {/* Phone call */}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.28 11 19.79 19.79 0 01.21 2.38 2 2 0 012.2 0h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.09 7.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"
              stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          {/* Three dots */}
          <svg width="4" height="16" viewBox="0 0 4 20" fill="white">
            <circle cx="2" cy="2" r="2"/><circle cx="2" cy="10" r="2"/><circle cx="2" cy="18" r="2"/>
          </svg>
        </div>
      </div>

      {/* ── Chat area ───────────────────────────────────────────── */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "12px 10px", display: "flex",
        flexDirection: "column", gap: 3,
        background: `${WA_BG} url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c8bfb4' fill-opacity='0.35'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
      }}>
        {/* Date chip */}
        {messages.length > 0 && (
          <div style={{ alignSelf: "center", background: "rgba(225,221,213,0.92)",
            padding: "3px 10px", borderRadius: 8, fontSize: 11, color: "#54656f",
            fontWeight: 500, marginBottom: 4, backdropFilter: "blur(4px)" }}>
            HOY
          </div>
        )}

        {messages.map((msg, i) => {
          const isUser = msg.type === "user";
          const prev = messages[i - 1];
          const isFirst = !prev || prev.type !== msg.type;

          return (
            <div key={msg.id} style={{
              display: "flex", justifyContent: isUser ? "flex-end" : "flex-start",
              marginTop: isFirst && i > 0 ? 6 : 1,
              paddingRight: isUser ? 0 : 4,
              paddingLeft: isUser ? 4 : 0,
            }}>
              <div style={{
                maxWidth: "78%", position: "relative",
                background: isUser ? WA_BUBBLE_OUT : "#fff",
                color: "#111b21",
                borderRadius: isUser
                  ? (isFirst ? "8px 8px 2px 8px" : "8px 8px 2px 8px")
                  : (isFirst ? "8px 8px 8px 2px" : "8px 8px 8px 2px"),
                padding: "6px 8px 4px",
                fontSize: 14, lineHeight: 1.45,
                boxShadow: "0 1px 2px rgba(0,0,0,0.13)",
              }}>
                {/* Bubble tail */}
                {isFirst && (
                  <div style={{
                    position: "absolute",
                    top: 0,
                    ...(isUser ? { right: -8 } : { left: -8 }),
                    width: 0, height: 0,
                    borderStyle: "solid",
                    borderWidth: isUser ? "8px 0 0 8px" : "8px 8px 0 0",
                    borderColor: isUser
                      ? `${WA_BUBBLE_OUT} transparent transparent transparent`
                      : `#fff transparent transparent transparent`,
                  }} />
                )}

                <span>{msg.text}</span>

                <div style={{
                  display: "flex", justifyContent: "flex-end", alignItems: "center",
                  gap: 3, marginTop: 2,
                }}>
                  <span style={{ fontSize: 10.5, color: isUser ? "#54a37e" : "#8696a0" }}>
                    {formatTime(msg.timestamp)}
                  </span>
                  {/* Double tick for user messages */}
                  {isUser && (
                    <svg width="16" height="10" viewBox="0 0 16 10" fill="none">
                      <path d="M1 5l3.5 3.5L10 1" stroke="#53bdeb" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M6 5l3.5 3.5L15 1" stroke="#53bdeb" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Typing indicator */}
        {disabled && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginTop: 4 }}>
            <div style={{
              background: "#fff", borderRadius: "8px 8px 8px 2px",
              padding: "10px 14px", boxShadow: "0 1px 2px rgba(0,0,0,0.13)",
              display: "flex", gap: 4, alignItems: "center",
            }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: 7, height: 7, borderRadius: "50%", background: "#8696a0",
                  animation: "waTyping 1.4s ease-in-out infinite",
                  animationDelay: `${i * 0.2}s`,
                }} />
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input area ─────────────────────────────────────────── */}
      <div style={{
        background: WA_BG, padding: "8px 10px",
        display: "flex", alignItems: "center", gap: 8, flexShrink: 0,
      }}>
        {/* Input pill */}
        <div style={{
          flex: 1, background: "#fff", borderRadius: 24,
          display: "flex", alignItems: "center", gap: 6,
          padding: "0 12px", boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
          minHeight: 42,
        }}>
          {/* Emoji icon */}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, color: "#8696a0" }}>
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8"/>
            <path d="M8 14s1.5 2 4 2 4-2 4-2" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            <circle cx="9" cy="10" r="1.2" fill="currentColor"/>
            <circle cx="15" cy="10" r="1.2" fill="currentColor"/>
          </svg>

          <input
            value={input}
            onChange={e => onInputChange(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !disabled && onSend()}
            placeholder="Escribí tu consulta..."
            disabled={disabled}
            style={{
              flex: 1, border: "none", outline: "none", fontSize: 14,
              background: "transparent", color: "#111b21", fontFamily: "inherit",
              padding: "10px 0",
            }}
          />

          {/* Attach icon */}
          {!hasText && (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, color: "#8696a0" }}>
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"
                stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
            </svg>
          )}
        </div>

        {/* Send / mic button */}
        <button
          onClick={onSend}
          disabled={disabled || !hasText}
          style={{
            width: 46, height: 46, borderRadius: "50%", border: "none", flexShrink: 0,
            background: hasText ? `linear-gradient(135deg, #25d366, ${WA_GREEN_LIGHT})` : WA_GREEN_LIGHT,
            color: "#fff", cursor: hasText && !disabled ? "pointer" : "default",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 6px rgba(0,0,0,0.25)",
            transition: "transform 0.15s, background 0.2s",
            opacity: disabled ? 0.7 : 1,
          }}
          onMouseEnter={e => { if (!disabled) (e.currentTarget as HTMLButtonElement).style.transform = "scale(1.08)"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.transform = "scale(1)"; }}
        >
          {hasText ? (
            /* Send icon */
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13" stroke="white" strokeWidth="2.2" strokeLinecap="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2z" stroke="white" strokeWidth="2.2" strokeLinejoin="round"/>
            </svg>
          ) : (
            /* Mic icon */
            <svg width="18" height="22" viewBox="0 0 18 22" fill="none">
              <rect x="5" y="1" width="8" height="13" rx="4" stroke="white" strokeWidth="1.8"/>
              <path d="M1 10c0 4.4 3.6 8 8 8s8-3.6 8-8" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
              <line x1="9" y1="18" x2="9" y2="21" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
              <line x1="6" y1="21" x2="12" y2="21" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
            </svg>
          )}
        </button>
      </div>

      {/* Typing animation keyframes */}
      <style>{`
        @keyframes waTyping {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>
    </>
  );
}

function TypingDots() {
  return (
    <span style={{ display: "inline-flex", gap: 2, alignItems: "center", marginLeft: 2 }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: 3, height: 3, borderRadius: "50%", background: "rgba(255,255,255,0.85)",
          display: "inline-block",
          animation: "waTyping 1.4s ease-in-out infinite",
          animationDelay: `${i * 0.2}s`,
        }} />
      ))}
    </span>
  );
}

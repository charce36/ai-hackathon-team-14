import { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

export default function PhoneFrame({ children }: Props) {
  const now = new Date();
  const time = now.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false });

  return (
    <div style={{
      width: 375, flexShrink: 0,
      background: "linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%)",
      borderRadius: 50, padding: "12px 10px 20px",
      boxShadow: "0 30px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1), 0 0 0 1px rgba(255,255,255,0.05)",
      display: "flex", flexDirection: "column",
      height: 760,
    }}>
      {/* Dynamic Island */}
      <div style={{
        height: 36, display: "flex", alignItems: "center", justifyContent: "center",
        flexShrink: 0, padding: "0 20px",
      }}>
        <div style={{
          width: 120, height: 34, borderRadius: 20,
          background: "#000",
          boxShadow: "inset 0 1px 3px rgba(0,0,0,0.8)",
          display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
        }}>
          {/* Camera */}
          <div style={{ width: 12, height: 12, borderRadius: "50%", background: "#1a1a1a",
            border: "1px solid #333", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 5, height: 5, borderRadius: "50%", background: "#2a2a4a", opacity: 0.7 }} />
          </div>
          {/* Sensor dot */}
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#1a1a2e", opacity: 0.5 }} />
        </div>
      </div>

      {/* Status bar */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "0 24px 4px", flexShrink: 0,
      }}>
        <span style={{ color: "#fff", fontSize: 12, fontWeight: 700, letterSpacing: "-0.3px",
          fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif" }}>{time}</span>
        <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
          {/* Signal */}
          <svg width="17" height="12" viewBox="0 0 17 12" fill="none">
            {[2, 4, 6, 8].map((h, i) => (
              <rect key={i} x={i * 4} y={12 - h} width="3" height={h} rx="1"
                fill={i < 3 ? "white" : "rgba(255,255,255,0.35)"} />
            ))}
          </svg>
          {/* WiFi */}
          <svg width="16" height="12" viewBox="0 0 16 12" fill="white">
            <path d="M8 9.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z" />
            <path d="M8 6.5C9.7 6.5 11.2 7.2 12.3 8.3l1.4-1.4A7.5 7.5 0 0 0 8 4.5a7.5 7.5 0 0 0-5.7 2.4L3.7 8.3C4.8 7.2 6.3 6.5 8 6.5z" opacity=".6" />
            <path d="M8 3.5c2.6 0 4.9 1.1 6.6 2.8l1.4-1.4A10.5 10.5 0 0 0 8 1.5a10.5 10.5 0 0 0-8 3.4l1.4 1.4C3.1 4.6 5.4 3.5 8 3.5z" opacity=".3" />
          </svg>
          {/* Battery */}
          <div style={{ display: "flex", alignItems: "center", gap: 1 }}>
            <div style={{ width: 25, height: 12, border: "1px solid rgba(255,255,255,0.5)",
              borderRadius: 3, padding: 2, position: "relative" }}>
              <div style={{ height: "100%", width: "75%", background: "#4cd964", borderRadius: 1 }} />
            </div>
            <div style={{ width: 2, height: 5, background: "rgba(255,255,255,0.4)", borderRadius: "0 1px 1px 0" }} />
          </div>
        </div>
      </div>

      {/* Screen */}
      <div style={{
        flex: 1, background: "#ece5dd", borderRadius: 38, overflow: "hidden",
        display: "flex", flexDirection: "column",
        boxShadow: "inset 0 0 0 1px rgba(0,0,0,0.15)",
      }}>
        {children}
      </div>

      {/* Home indicator */}
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 10, flexShrink: 0 }}>
        <div style={{ width: 130, height: 5, background: "rgba(255,255,255,0.3)", borderRadius: 3 }} />
      </div>
    </div>
  );
}

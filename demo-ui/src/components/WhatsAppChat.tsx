import { ClientMessage } from "../api";

interface Props {
  messages: ClientMessage[];
  input: string;
  onInputChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
}

export default function WhatsAppChat({
  messages,
  input,
  onInputChange,
  onSend,
  disabled,
}: Props) {
  return (
    <>
      <div className="wa-header">
        <h2>Soporte QuintoAndar</h2>
        <p>en línea</p>
      </div>
      <div className="wa-chat">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`bubble ${msg.type === "user" ? "user" : "bot"}`}
          >
            {msg.text}
            <div className="bubble-time">{formatTime(msg.timestamp)}</div>
          </div>
        ))}
      </div>
      <div className="wa-input-area">
        <div className="input-row">
          <input
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSend()}
            placeholder="Escribí tu consulta..."
            disabled={disabled}
          />
          <button onClick={onSend} disabled={disabled || !input.trim()}>
            Enviar
          </button>
        </div>
      </div>
    </>
  );
}

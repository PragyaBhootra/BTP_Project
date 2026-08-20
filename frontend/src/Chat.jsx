import { useState } from "react";

const API_URL = import.meta.env.VITE_API_URL;

export default function Chat({ user }) {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Tell me what happened, and where." },
  ]);
  const [complaintData, setComplaintData] = useState({});
  const [input, setInput] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const [status, setStatus] = useState(null); // null | "sending" | "sent" | "error"

  async function sendMessage() {
    const text = input.trim();
    if (!text || isComplete) return;

    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");

    const res = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, complaint_data: complaintData }),
    });
    const data = await res.json();

    setComplaintData(data.complaint_data);
    setIsComplete(data.is_complete);
    setMessages((m) => [...m, { role: "bot", text: data.reply }]);
  }

  async function submitComplaint() {
    setStatus("sending");
    try {
      const classifyRes = await fetch(`${API_URL}/api/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ complaint_data: complaintData }),
      });
      const { department } = await classifyRes.json();

      setMessages((m) => [
        ...m,
        { role: "bot", text: `Routing this to: ${department.replace("_", " ")}` },
      ]);

      const sendRes = await fetch(`${API_URL}/api/send-complaint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          department,
          complaint_data: complaintData,
          user_email: user.email,
        }),
      });
      const result = await sendRes.json();
      setStatus(result.success ? "sent" : "error");

      if (result.success && result.advice) {
        setMessages((m) => [...m, { role: "bot", text: result.advice }]);
      }
    } catch (e) {
      console.error(e);
      setStatus("error");
    }
  }

  return (
    <div className="chat-card">
      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`bubble bubble-${m.role}`}>
            {m.text}
          </div>
        ))}
      </div>

      {!isComplete ? (
        <div className="chat-input-row">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Type your message..."
          />
          <button onClick={sendMessage}>Send</button>
        </div>
      ) : (
        <div className="chat-submit-row">
          {status === "sent" ? (
            <p className="status-ok">Complaint sent. You'll be contacted at {user.email}.</p>
          ) : status === "error" ? (
            <p className="status-err">Something went wrong — try again.</p>
          ) : (
            <button onClick={submitComplaint} disabled={status === "sending"}>
              {status === "sending" ? "Sending..." : "Send Complaint"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

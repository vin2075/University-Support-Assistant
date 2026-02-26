import { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import ChatWindow from "./components/ChatWindow";
import Sidebar from "./components/Sidebar";

const SESSION_KEY = "rag_session_id";

function getOrCreateSession() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = uuidv4();
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

const WELCOME = {
  id: "welcome",
  role: "assistant",
  content:
    "👋 Hello! I'm the **University Support Assistant**. I can answer questions about university policies, registration, housing, financial aid, and more.\n\nWhat can I help you with today?",
  timestamp: new Date().toISOString(),
};

export default function App() {
  const [sessionId, setSessionId] = useState(getOrCreateSession);
  const [messages,  setMessages]  = useState([WELCOME]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastMeta,  setLastMeta]  = useState(null);

  // ── Send a message (used by InputBar AND suggested questions) ──────────────
  const handleSend = async (text) => {
    if (!text.trim() || isLoading) return;

    setMessages((prev) => [
      ...prev,
      { id: uuidv4(), role: "user", content: text, timestamp: new Date().toISOString() },
    ]);
    setIsLoading(true);

    try {
      const res  = await fetch("/api/chat", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ sessionId, message: text }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Server error " + res.status);

      setMessages((prev) => [
        ...prev,
        { id: uuidv4(), role: "assistant", content: data.reply, timestamp: new Date().toISOString() },
      ]);
      setLastMeta({
        tokensUsed:      data.tokensUsed,
        retrievedChunks: data.retrievedChunks,
        scores:          data.scores,
      });
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(), role: "assistant", isError: true,
          content: `⚠️ **Error:** ${err.message || "Something went wrong."}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // ── New chat ───────────────────────────────────────────────────────────────
  const handleNewChat = () => {
    const newId = uuidv4();
    localStorage.setItem(SESSION_KEY, newId);
    setSessionId(newId);
    setMessages([{ ...WELCOME, id: uuidv4(), timestamp: new Date().toISOString() }]);
    setLastMeta(null);
    fetch(`/api/session/${newId}`, { method: "DELETE" }).catch(() => {});
  };

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      {/* Pass onSend so suggested questions can trigger it */}
      <Sidebar
        sessionId={sessionId}
        onNewChat={handleNewChat}
        onSend={handleSend}
        lastMeta={lastMeta}
      />

      <div className="flex flex-col flex-1 min-w-0">
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-3 shadow-sm flex-shrink-0">
          <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-xl">
            🎓
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-800 leading-tight">
              University RAG Assistant
            </h1>
            <p className="text-xs text-slate-500">
              Powered by OpenRouter + sentence-transformers
            </p>
          </div>
        </header>

        <ChatWindow messages={messages} isLoading={isLoading} onSend={handleSend} />
      </div>
    </div>
  );
}
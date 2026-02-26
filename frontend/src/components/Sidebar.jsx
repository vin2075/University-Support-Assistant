const SUGGESTED_QUESTIONS = [
  "How do I reset my password?",
  "What is the late payment fee for tuition?",
  "How many absences are allowed per semester?",
  "What happens if I plagiarize?",
  "How do I drop a course?",
  "What are library borrowing limits?",
];

export default function Sidebar({ sessionId, onNewChat, onSend, lastMeta }) {
  return (
    <aside className="w-64 bg-slate-800 text-white flex flex-col flex-shrink-0 overflow-y-auto">
      {/* Branding */}
      <div className="p-5 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-2xl">🎓</span>
          <span className="font-bold text-base leading-tight">
            University<br />RAG Assistant
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          Retrieval-Augmented Generation<br />powered by OpenRouter
        </p>
      </div>

      {/* New Chat button */}
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="
            w-full py-2 px-4 rounded-lg border border-slate-600
            text-sm font-medium text-slate-300
            hover:bg-slate-700 hover:text-white
            active:scale-[0.98] transition-all duration-150
            flex items-center justify-center gap-2
          "
        >
          <span>＋</span> New Chat
        </button>
      </div>

      {/* Suggested questions — clicking sends to chat */}
      <div className="px-4 pb-4">
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2 font-semibold">
          Suggested Questions
        </p>
        <div className="space-y-1.5">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => onSend(q)}
              className="
                w-full text-left text-xs text-slate-400 px-3 py-2 rounded-lg
                hover:bg-slate-700 hover:text-white
                active:bg-slate-600
                transition-colors duration-100 leading-snug cursor-pointer
              "
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-slate-700 mx-4" />

      {/* Last response metadata */}
      {lastMeta && (
        <div className="p-4 mt-2">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2 font-semibold">
            Last Response
          </p>
          <div className="space-y-1.5 text-xs text-slate-400">
            <div className="flex justify-between">
              <span>Chunks Retrieved</span>
              <span className="text-blue-400 font-mono">{lastMeta.retrievedChunks}</span>
            </div>
            <div className="flex justify-between">
              <span>Tokens Used</span>
              <span className="text-blue-400 font-mono">{lastMeta.tokensUsed}</span>
            </div>
            {lastMeta.scores?.length > 0 && (
              <div className="mt-2">
                <p className="text-[10px] text-slate-500 mb-1">Similarity Scores</p>
                {lastMeta.scores.map((score, i) => (
                  <div key={i} className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] w-4">#{i + 1}</span>
                    <div className="flex-1 bg-slate-700 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${Math.min(score * 100, 100)}%` }}
                      />
                    </div>
                    <span className="font-mono text-[10px]">{score.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Session ID */}
      <div className="mt-auto p-4 border-t border-slate-700">
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 font-semibold">
          Session ID
        </p>
        <p className="text-[10px] font-mono text-slate-500 break-all">
          {sessionId?.slice(0, 18)}…
        </p>
      </div>
    </aside>
  );
}
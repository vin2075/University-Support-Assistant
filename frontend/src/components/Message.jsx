import ReactMarkdown from "react-markdown";

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function Message({ message }) {
  const isUser = message.role === "user";
  const isError = message.isError;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} gap-3`}>
      {/* Avatar — assistant only */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold mt-1">
          🎓
        </div>
      )}

      <div
        className={`
          max-w-[75%] rounded-2xl px-4 py-3 shadow-sm
          ${isUser
            ? "bg-blue-600 text-white rounded-br-md"
            : isError
            ? "bg-red-50 border border-red-200 text-red-800 rounded-bl-md"
            : "bg-white text-slate-800 border border-slate-200 rounded-bl-md"
          }
        `}
      >
        {/* Markdown content */}
        <div
          className={`
            prose prose-sm max-w-none
            ${isUser ? "prose-invert" : ""}
          `}
        >
          <ReactMarkdown
            components={{
              // Remove wrapping <p> margins inside the bubble
              p: ({ children }) => (
                <p className="mb-1 last:mb-0">{children}</p>
              ),
              strong: ({ children }) => (
                <strong className={isUser ? "text-blue-100" : "text-slate-900"}>
                  {children}
                </strong>
              ),
              ul: ({ children }) => (
                <ul className="list-disc pl-4 mt-1">{children}</ul>
              ),
              li: ({ children }) => (
                <li className="mb-0.5">{children}</li>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Timestamp */}
        <p
          className={`
            text-[10px] mt-1.5 text-right select-none
            ${isUser ? "text-blue-200" : "text-slate-400"}
          `}
        >
          {formatTime(message.timestamp)}
        </p>
      </div>

      {/* Avatar — user only */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-white text-sm font-bold mt-1">
          U
        </div>
      )}
    </div>
  );
}

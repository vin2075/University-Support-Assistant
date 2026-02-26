import { useState, useRef } from "react";

export default function InputBar({ onSend, isLoading }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const canSend = text.trim().length > 0 && !isLoading;

  const handleSend = () => {
    if (!canSend) return;
    onSend(text.trim());
    setText("");
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    // Send on Enter (no Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-grow textarea
  const handleInput = (e) => {
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
    setText(el.value);
  };

  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3">
      <div className="flex items-end gap-3 max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={text}
            onInput={handleInput}
            onKeyDown={handleKeyDown}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ask about university policies, registration, housing…"
            rows={1}
            disabled={isLoading}
            className="
              w-full resize-none rounded-xl border border-slate-300 bg-slate-50
              px-4 py-3 pr-12 text-sm text-slate-800 placeholder-slate-400
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-150
            "
          />
          {/* Character count hint */}
          {text.length > 1800 && (
            <span className="absolute bottom-1 right-2 text-[10px] text-orange-500">
              {2000 - text.length} left
            </span>
          )}
        </div>

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!canSend}
          aria-label="Send message"
          className="
            flex-shrink-0 w-11 h-11 rounded-xl bg-blue-600 text-white
            flex items-center justify-center shadow
            hover:bg-blue-700 active:scale-95
            disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-blue-600
            transition-all duration-150
          "
        >
          {isLoading ? (
            <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
              <circle
                className="opacity-25"
                cx="12" cy="12" r="10"
                stroke="currentColor" strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v8H4z"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          )}
        </button>
      </div>

      <p className="text-center text-[10px] text-slate-400 mt-2">
        Press <kbd className="bg-slate-100 px-1 rounded text-slate-500">Enter</kbd> to send
        · <kbd className="bg-slate-100 px-1 rounded text-slate-500">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}

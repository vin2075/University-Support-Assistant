export default function TypingIndicator() {
  return (
    <div className="flex justify-start gap-3">
      {/* Bot avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold mt-1">
        🎓
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm flex items-center gap-1.5">
        <span className="text-xs text-slate-500 mr-1">Thinking</span>
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dot-1 inline-block" />
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dot-2 inline-block" />
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dot-3 inline-block" />
      </div>
    </div>
  );
}

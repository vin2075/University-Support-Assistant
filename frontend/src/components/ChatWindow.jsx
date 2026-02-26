import { useEffect, useRef } from "react";
import Message from "./Message";
import InputBar from "./InputBar";
import TypingIndicator from "./TypingIndicator";

export default function ChatWindow({ messages, isLoading, onSend }) {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom when messages or loading state change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto chat-scroll px-4 py-6 space-y-4">
        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
        ))}

        {/* Loading / typing indicator */}
        {isLoading && <TypingIndicator />}

        {/* Invisible anchor to scroll to */}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <InputBar onSend={onSend} isLoading={isLoading} />
    </div>
  );
}

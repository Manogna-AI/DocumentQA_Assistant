import { useEffect, useRef } from 'react';
import { MessageSquare } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';

export default function ChatPanel() {
  const messages = useAppStore((s) => s.messages);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <main className="flex flex-col min-w-0 bg-white dark:bg-gray-950">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-3">
            <MessageSquare size={48} strokeWidth={1} />
            <p className="text-lg font-medium">Ask anything about your documents</p>
            <p className="text-sm">Upload a document first, then ask questions here.</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
      <ChatInput />
    </main>
  );
}

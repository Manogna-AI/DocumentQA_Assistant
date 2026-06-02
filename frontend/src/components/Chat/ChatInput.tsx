import { useState, useRef, useEffect } from 'react';
import { SendHorizonal } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import { useChat } from '@/hooks/useChat';

export default function ChatInput() {
  const [text, setText] = useState('');
  const isQuerying = useAppStore((s) => s.isQuerying);
  const { send } = useChat();
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { ref.current?.focus(); }, []);

  const handleSend = () => {
    if (!text.trim() || isQuerying) return;
    send(text.trim());
    setText('');
    setTimeout(() => ref.current?.focus(), 50);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 dark:border-gray-800 p-3">
      <div className="flex items-end gap-2 bg-gray-100 dark:bg-gray-800 rounded-xl px-3 py-2">
        <textarea
          ref={ref}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your document..."
          rows={1}
          className="flex-1 bg-transparent resize-none outline-none text-sm placeholder:text-gray-400 max-h-32"
        />
        <button
          onClick={handleSend}
          disabled={!text.trim() || isQuerying}
          className="p-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <SendHorizonal size={16} />
        </button>
      </div>
      <p className="text-[10px] text-gray-400 mt-1.5 text-center">
        Answers are generated from uploaded documents only. Press Enter to send, Shift+Enter for new line.
      </p>
    </div>
  );
}

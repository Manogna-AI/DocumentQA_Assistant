import { useState, useRef, useEffect } from 'react';
import { SendHorizonal, Timer } from 'lucide-react';
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
    <div className="border-t border-slate-200/80 bg-white/80 p-4 backdrop-blur dark:border-slate-800/80 dark:bg-slate-950/70">
      <div className="mx-auto max-w-4xl rounded-3xl border border-slate-200 bg-white p-2 shadow-xl shadow-slate-200/60 transition focus-within:border-blue-300 focus-within:ring-4 focus-within:ring-blue-500/10 dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/20 dark:focus-within:border-blue-700">
        <div className="flex items-end gap-2">
          <textarea
            ref={ref}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question, request a summary, or compare document sections..."
            rows={1}
            className="max-h-36 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-100"
          />
          <button
            onClick={handleSend}
            disabled={!text.trim() || isQuerying}
            className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
            title="Send message"
          >
            <SendHorizonal size={18} />
          </button>
        </div>
      </div>
      <div className="mx-auto mt-2 flex max-w-4xl flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[11px] text-slate-400">
        <span>Answers are generated from uploaded documents only.</span>
        <span className="inline-flex items-center gap-1">
          <Timer size={12} /> Extended Ollama timeout enabled for slower local models.
        </span>
        <span>Enter to send · Shift+Enter for a new line</span>
      </div>
    </div>
  );
}

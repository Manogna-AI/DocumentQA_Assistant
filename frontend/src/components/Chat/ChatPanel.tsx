import { useEffect, useRef } from 'react';
import { MessageSquare, ShieldCheck, UploadCloud } from 'lucide-react';
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
    <main className="flex min-h-0 min-w-0 flex-col overflow-hidden bg-white/90 dark:bg-slate-950/60">
      <div className="shrink-0 border-b border-slate-200/80 bg-white/70 px-5 py-3 backdrop-blur dark:border-slate-800/80 dark:bg-slate-950/40">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
              Research Copilot
            </p>
            <h2 className="mt-1 text-base font-bold text-slate-900 dark:text-white">
              Ask, compare, summarize
            </h2>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300">
            <ShieldCheck size={14} /> Citation-first answers
          </span>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-5 sm:px-6 lg:px-8">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center">
            <div className="max-w-xl rounded-[2rem] border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-8 text-center shadow-xl shadow-slate-200/70 dark:border-slate-800 dark:from-slate-900 dark:to-slate-950 dark:shadow-black/20">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-blue-600 text-white shadow-lg shadow-blue-600/25">
                <MessageSquare size={30} strokeWidth={1.8} />
              </div>
              <h3 className="mt-5 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                Start a grounded document conversation
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">
                Upload your source material, then ask precise questions. The assistant will retrieve
                relevant excerpts and show citations for traceability.
              </p>
              <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                <UploadCloud size={14} /> Supports PDF, DOCX, and PPTX files
              </div>
            </div>
          </div>
        )}
        <div className="mx-auto max-w-4xl space-y-5 pb-2">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} />
        </div>
      </div>
      <ChatInput />
    </main>
  );
}

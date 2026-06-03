import ReactMarkdown from 'react-markdown';
import { clsx } from 'clsx';
import { User, Bot, Sparkles } from 'lucide-react';
import type { Message } from '@/types/chat';
import { useAppStore } from '@/stores/appStore';
import LoadingDots from './LoadingDots';

export default function MessageBubble({ message }: { message: Message }) {
  const setCitations = useAppStore((s) => s.setCitations);
  const isUser = message.role === 'user';

  return (
    <div className={clsx('flex min-w-0 gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-slate-800 to-blue-700 text-white shadow-lg shadow-blue-900/15 dark:from-blue-600 dark:to-cyan-600">
          <Bot size={17} />
        </div>
      )}
      <div
        className={clsx(
          'min-w-0 max-w-[82%] overflow-hidden rounded-[1.35rem] px-4 py-3 text-sm leading-relaxed shadow-sm sm:max-w-[78%]',
          isUser
            ? 'rounded-br-md bg-gradient-to-br from-blue-600 to-cyan-600 text-white shadow-blue-600/20'
            : 'rounded-bl-md border border-slate-200 bg-white text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200',
        )}
      >
        {message.isLoading ? (
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-300">
            <Sparkles size={15} className="text-blue-500" />
            <span className="text-xs font-semibold">Ollama is analyzing your documents</span>
            <LoadingDots />
          </div>
        ) : isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose-chat">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {message.citations && message.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5 border-t border-slate-200 pt-3 dark:border-slate-800">
                {message.citations.map((c, i) => (
                  <button
                    key={c.chunk_id}
                    onClick={() => setCitations(message.citations!)}
                    className="rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-bold text-blue-700 ring-1 ring-blue-200 transition hover:bg-blue-100 dark:bg-blue-950/50 dark:text-blue-300 dark:ring-blue-900 dark:hover:bg-blue-900/60"
                  >
                    [{i + 1}] p.{c.page_number ?? '?'}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {isUser && (
        <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-lg shadow-slate-900/15 dark:bg-slate-700">
          <User size={17} />
        </div>
      )}
    </div>
  );
}

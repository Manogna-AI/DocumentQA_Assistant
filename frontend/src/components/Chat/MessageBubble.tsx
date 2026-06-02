import ReactMarkdown from 'react-markdown';
import { clsx } from 'clsx';
import { User, Bot } from 'lucide-react';
import type { Message } from '@/types/chat';
import { useAppStore } from '@/stores/appStore';
import LoadingDots from './LoadingDots';

export default function MessageBubble({ message }: { message: Message }) {
  const setCitations = useAppStore((s) => s.setCitations);
  const isUser = message.role === 'user';

  return (
    <div className={clsx('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center shrink-0 mt-0.5">
          <Bot size={15} />
        </div>
      )}
      <div
        className={clsx(
          'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-blue-600 text-white rounded-br-md'
            : 'bg-gray-100 dark:bg-gray-800 rounded-bl-md',
        )}
      >
        {message.isLoading ? (
          <LoadingDots />
        ) : isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose-chat">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {message.citations && message.citations.length > 0 && (
              <div className="flex gap-1 mt-2 flex-wrap">
                {message.citations.map((c, i) => (
                  <button
                    key={c.chunk_id}
                    onClick={() => setCitations(message.citations!)}
                    className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
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
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-0.5">
          <User size={15} className="text-white" />
        </div>
      )}
    </div>
  );
}

import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { clsx } from 'clsx';
import type { Citation } from '@/types/chat';

function ScoreBar({ score }: { score: number | null }) {
  const pct = Math.round((score ?? 0) * 100);
  const color = pct >= 80 ? 'bg-green-500' : pct >= 60 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-gray-500">{pct}%</span>
    </div>
  );
}

export default function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-2.5">
      <div className="flex items-start justify-between gap-1">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="shrink-0 w-5 h-5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-[10px] flex items-center justify-center font-bold">
            {index}
          </span>
          <FileText size={12} className="shrink-0 text-gray-400" />
          <span className="text-xs font-medium truncate">{citation.document_name}</span>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {citation.page_number && (
            <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-full">
              p.{citation.page_number}
            </span>
          )}
          {citation.slide_number && (
            <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded-full">
              slide {citation.slide_number}
            </span>
          )}
        </div>
      </div>

      <div className="mt-1.5">
        <ScoreBar score={citation.score} />
      </div>

      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-0.5 text-[10px] text-blue-600 dark:text-blue-400 mt-1.5 hover:underline"
      >
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        {expanded ? 'Hide' : 'Show'} excerpt
      </button>

      {expanded && (
        <p className="mt-1.5 text-xs text-gray-600 dark:text-gray-400 leading-relaxed bg-gray-50 dark:bg-gray-900 rounded p-2 max-h-40 overflow-y-auto">
          {citation.snippet || 'No text available'}
        </p>
      )}
    </div>
  );
}

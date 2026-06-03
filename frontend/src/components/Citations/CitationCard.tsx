import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, Gauge } from 'lucide-react';
import { clsx } from 'clsx';
import type { Citation } from '@/types/chat';

function ScoreBar({ score }: { score: number | null }) {
  const pct = Math.round((score ?? 0) * 100);
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="flex items-center gap-2">
      <Gauge size={12} className="text-slate-400" />
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-[10px] font-bold text-slate-500">{pct}%</span>
    </div>
  );
}

export default function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/90 p-3.5 shadow-sm transition hover:border-blue-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-blue-900">
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-start gap-2">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-[11px] font-bold text-white shadow-sm shadow-blue-600/20">
            {index}
          </span>
          <div className="min-w-0">
            <div className="flex min-w-0 items-center gap-1.5">
              <FileText size={13} className="shrink-0 text-slate-400" />
              <span className="truncate text-xs font-bold text-slate-800 dark:text-slate-100" title={citation.document_name}>
                {citation.document_name}
              </span>
            </div>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {citation.page_number && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                  Page {citation.page_number}
                </span>
              )}
              {citation.slide_number && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                  Slide {citation.slide_number}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-3">
        <ScoreBar score={citation.score} />
      </div>

      <button
        onClick={() => setExpanded((v) => !v)}
        className="mt-3 inline-flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-bold text-blue-700 transition hover:bg-blue-50 dark:text-blue-300 dark:hover:bg-blue-950/50"
      >
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        {expanded ? 'Hide' : 'Show'} excerpt
      </button>

      {expanded && (
        <p className="mt-2 max-h-44 overflow-y-auto rounded-2xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-800">
          {citation.snippet || 'No text available'}
        </p>
      )}
    </div>
  );
}

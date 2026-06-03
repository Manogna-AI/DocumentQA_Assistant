import { BookOpen, Quote } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import CitationCard from './CitationCard';

export default function CitationPanel() {
  const citations = useAppStore((s) => s.citations);

  return (
    <aside className="hidden flex-col overflow-hidden border-l border-slate-200/80 bg-slate-50/80 dark:border-slate-800/80 dark:bg-slate-900/50 xl:flex">
      <div className="border-b border-slate-200/80 px-4 py-4 dark:border-slate-800/80">
        <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
          Evidence
        </p>
        <h2 className="mt-1 flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
          <BookOpen size={16} /> Citations ({citations.length})
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {citations.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/60 p-5 text-center dark:border-slate-700 dark:bg-slate-950/40">
            <Quote size={28} className="mx-auto text-slate-300 dark:text-slate-600" />
            <p className="mt-3 text-sm font-semibold text-slate-600 dark:text-slate-300">No citations yet</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">
              Source excerpts will appear here after an answer includes supporting evidence.
            </p>
          </div>
        )}
        {citations.map((c, i) => (
          <CitationCard key={c.chunk_id} citation={c} index={i + 1} />
        ))}
      </div>
    </aside>
  );
}

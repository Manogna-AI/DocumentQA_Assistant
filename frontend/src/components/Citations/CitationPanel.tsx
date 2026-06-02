import { BookOpen } from 'lucide-react';
import { useAppStore } from '@/stores/appStore';
import CitationCard from './CitationCard';

export default function CitationPanel() {
  const citations = useAppStore((s) => s.citations);

  return (
    <aside className="flex flex-col border-l border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 overflow-hidden">
      <div className="px-3 py-2.5 border-b border-gray-200 dark:border-gray-800">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
          <BookOpen size={15} /> Citations ({citations.length})
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {citations.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-8">
            Citations will appear here
            <br />
            after you ask a question.
          </p>
        )}
        {citations.map((c, i) => (
          <CitationCard key={c.chunk_id} citation={c} index={i + 1} />
        ))}
      </div>
    </aside>
  );
}

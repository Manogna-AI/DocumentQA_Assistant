import { FileText, Trash2, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import type { DocumentInfo } from '@/types/document';
import { useAppStore } from '@/stores/appStore';
import { useDeleteDocument } from '@/hooks/useDocuments';

const statusStyles: Record<string, string> = {
  indexed: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:ring-emerald-900',
  processing: 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:ring-amber-900',
  failed: 'bg-red-50 text-red-700 ring-red-200 dark:bg-red-950/50 dark:text-red-300 dark:ring-red-900',
};

function StatusIcon({ status }: { status: string }) {
  if (status === 'indexed') return <CheckCircle2 size={12} />;
  if (status === 'processing') return <Loader2 size={12} className="animate-spin" />;
  if (status === 'failed') return <AlertTriangle size={12} />;
  return null;
}

export default function DocumentCard({ doc }: { doc: DocumentInfo }) {
  const { selectedDocumentId, setSelectedDocumentId } = useAppStore();
  const deleteMut = useDeleteDocument();
  const isSelected = selectedDocumentId === doc.document_id;

  return (
    <div
      onClick={() => setSelectedDocumentId(doc.document_id)}
      className={clsx(
        'group cursor-pointer rounded-2xl border p-3.5 transition-all duration-200',
        isSelected
          ? 'border-blue-300 bg-blue-50 shadow-lg shadow-blue-600/10 ring-2 ring-blue-500/10 dark:border-blue-800 dark:bg-blue-950/40'
          : 'border-slate-200 bg-white/80 shadow-sm hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-950/60 dark:hover:border-blue-900',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-start gap-2.5">
          <div className={clsx('mt-0.5 rounded-xl p-2', isSelected ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300')}>
            <FileText size={15} />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-800 dark:text-slate-100" title={doc.document_name}>
              {doc.document_name}
            </p>
            <p className="mt-1 text-[11px] text-slate-400">ID {doc.document_id.slice(0, 10)}...</p>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm('Delete this document?')) deleteMut.mutate(doc.document_id);
          }}
          className="rounded-lg p-1.5 text-slate-400 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 dark:hover:bg-red-950/60 dark:hover:text-red-300"
          title="Delete document"
        >
          <Trash2 size={14} />
        </button>
      </div>
      <div className="mt-3 flex items-center justify-between gap-2">
        <span className={clsx('inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wide ring-1', statusStyles[doc.status] ?? statusStyles.failed)}>
          <StatusIcon status={doc.status} />
          {doc.status}
        </span>
        {doc.chunk_count > 0 && (
          <span className="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-400">
            {doc.chunk_count} chunks
          </span>
        )}
      </div>
    </div>
  );
}

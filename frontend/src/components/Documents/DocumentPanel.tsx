import { FileText, Layers3 } from 'lucide-react';
import { useDocumentList } from '@/hooks/useDocuments';
import DocumentCard from './DocumentCard';

export default function DocumentPanel() {
  const { data, isLoading } = useDocumentList();
  const documents = data?.documents ?? [];

  return (
    <aside className="flex min-h-[220px] flex-col overflow-hidden border-b border-slate-200/80 bg-slate-50/80 dark:border-slate-800/80 dark:bg-slate-900/50 lg:border-b-0 lg:border-r">
      <div className="border-b border-slate-200/80 px-4 py-4 dark:border-slate-800/80">
        <div className="flex items-center justify-between gap-2">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">
              Knowledge Base
            </p>
            <h2 className="mt-1 flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
              <FileText size={16} /> Documents
            </h2>
          </div>
          <span className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-600 shadow-sm ring-1 ring-slate-200 dark:bg-slate-950 dark:text-slate-300 dark:ring-slate-800">
            <Layers3 size={13} /> {documents.length}
          </span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {isLoading && (
          <p className="rounded-2xl border border-dashed border-slate-300 p-5 text-center text-sm text-slate-400 dark:border-slate-700">
            Loading documents...
          </p>
        )}
        {!isLoading && documents.length === 0 && (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white/60 p-5 text-center dark:border-slate-700 dark:bg-slate-950/40">
            <FileText size={28} className="mx-auto text-slate-300 dark:text-slate-600" />
            <p className="mt-3 text-sm font-semibold text-slate-600 dark:text-slate-300">No documents yet</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">
              Upload a PDF, DOCX, or PPTX to build a searchable document workspace.
            </p>
          </div>
        )}
        {documents.map((doc) => (
          <DocumentCard key={doc.document_id} doc={doc} />
        ))}
      </div>
    </aside>
  );
}

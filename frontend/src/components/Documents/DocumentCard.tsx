import { FileText, Trash2, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import type { DocumentInfo } from '@/types/document';
import { useAppStore } from '@/stores/appStore';
import { useDeleteDocument } from '@/hooks/useDocuments';

const statusColors: Record<string, string> = {
  indexed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  processing: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
};

export default function DocumentCard({ doc }: { doc: DocumentInfo }) {
  const { selectedDocumentId, setSelectedDocumentId } = useAppStore();
  const deleteMut = useDeleteDocument();
  const isSelected = selectedDocumentId === doc.document_id;

  return (
    <div
      onClick={() => setSelectedDocumentId(doc.document_id)}
      className={clsx(
        'p-2.5 rounded-lg cursor-pointer transition-colors group',
        isSelected
          ? 'bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800'
          : 'hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent',
      )}
    >
      <div className="flex items-start justify-between gap-1">
        <div className="flex items-center gap-1.5 min-w-0">
          <FileText size={14} className="shrink-0 text-gray-400" />
          <span className="text-sm font-medium truncate">{doc.document_name}</span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm('Delete this document?')) deleteMut.mutate(doc.document_id);
          }}
          className="opacity-0 group-hover:opacity-100 p-0.5 text-gray-400 hover:text-red-500"
        >
          <Trash2 size={13} />
        </button>
      </div>
      <div className="flex items-center gap-2 mt-1.5">
        <span className={clsx('text-[10px] px-1.5 py-0.5 rounded-full font-medium', statusColors[doc.status])}>
          {doc.status === 'processing' && <Loader2 size={10} className="inline mr-0.5 animate-spin" />}
          {doc.status}
        </span>
        {doc.chunk_count > 0 && (
          <span className="text-[10px] text-gray-400">{doc.chunk_count} chunks</span>
        )}
      </div>
    </div>
  );
}

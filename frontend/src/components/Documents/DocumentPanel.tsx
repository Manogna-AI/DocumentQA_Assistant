import { FileText } from 'lucide-react';
import { useDocumentList } from '@/hooks/useDocuments';
import DocumentCard from './DocumentCard';

export default function DocumentPanel() {
  const { data, isLoading } = useDocumentList();
  const documents = data?.documents ?? [];

  return (
    <aside className="flex flex-col border-r border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 overflow-hidden">
      <div className="px-3 py-2.5 border-b border-gray-200 dark:border-gray-800">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
          <FileText size={15} /> Documents
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {isLoading && (
          <p className="text-xs text-gray-400 text-center py-4">Loading...</p>
        )}
        {!isLoading && documents.length === 0 && (
          <p className="text-xs text-gray-400 text-center py-8">
            No documents yet.
            <br />
            Click Upload to add one.
          </p>
        )}
        {documents.map((doc) => (
          <DocumentCard key={doc.document_id} doc={doc} />
        ))}
      </div>
    </aside>
  );
}

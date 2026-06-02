import { useHealth } from '@/hooks/useHealth';
import { useAppStore } from '@/stores/appStore';

export default function StatusBar() {
  const { data } = useHealth();
  const selectedDocId = useAppStore((s) => s.selectedDocumentId);

  return (
    <footer className="flex items-center justify-between px-4 py-1.5 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 text-xs text-gray-500">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${data?.api ? 'bg-green-500' : 'bg-red-500'}`} />
          API {data?.api ? 'Connected' : 'Offline'}
        </span>
        <span className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${data?.ollama ? 'bg-green-500' : 'bg-red-500'}`} />
          Ollama {data?.ollama ? 'Running' : 'Offline'}
        </span>
      </div>
      <span>{selectedDocId ? `Document: ${selectedDocId.slice(0, 8)}...` : 'No document selected'}</span>
    </footer>
  );
}

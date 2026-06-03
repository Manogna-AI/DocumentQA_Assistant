import { Activity, Database, FileCheck2 } from 'lucide-react';
import { useHealth } from '@/hooks/useHealth';
import { useAppStore } from '@/stores/appStore';

export default function StatusBar() {
  const { data } = useHealth();
  const selectedDocId = useAppStore((s) => s.selectedDocumentId);

  return (
    <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200/80 bg-slate-50/90 px-5 py-2.5 text-xs text-slate-500 backdrop-blur dark:border-slate-800/80 dark:bg-slate-900/70 dark:text-slate-400">
      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1 shadow-sm dark:border-slate-800 dark:bg-slate-950">
          <Activity size={13} className={data?.api ? 'text-emerald-500' : 'text-red-500'} />
          API {data?.api ? 'Connected' : 'Offline'}
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-2.5 py-1 shadow-sm dark:border-slate-800 dark:bg-slate-950">
          <Database size={13} className={data?.ollama ? 'text-emerald-500' : 'text-red-500'} />
          Ollama {data?.ollama ? 'Running' : 'Offline'}
        </span>
      </div>
      <span className="inline-flex items-center gap-1.5 truncate">
        <FileCheck2 size={13} />
        {selectedDocId ? `Active document: ${selectedDocId.slice(0, 12)}...` : 'No document selected'}
      </span>
    </footer>
  );
}

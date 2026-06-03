import { FileUp, Moon, Sparkles, Sun, Trash2 } from 'lucide-react';
import { useRef } from 'react';
import { useAppStore } from '@/stores/appStore';
import { useUploadDocument } from '@/hooks/useDocuments';
import { toast } from 'sonner';

const ALLOWED_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
];
const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

export default function Header() {
  const { theme, toggleTheme, clearMessages } = useAppStore();
  const fileRef = useRef<HTMLInputElement>(null);
  const upload = useUploadDocument();

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!ALLOWED_TYPES.includes(file.type)) {
      toast.error('Unsupported file type. Allowed: PDF, DOCX, PPTX');
      return;
    }
    if (file.size > MAX_SIZE) {
      toast.error('File exceeds 50 MB limit');
      return;
    }
    upload.mutate(file);
    e.target.value = '';
  };

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 bg-white/85 px-5 py-4 backdrop-blur-xl dark:border-slate-800/80 dark:bg-slate-950/75">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-cyan-500 shadow-lg shadow-blue-600/25">
          <Sparkles size={20} className="text-white" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="truncate text-xl font-bold tracking-tight text-slate-950 dark:text-white">
              DocQA Assistant
            </h1>
            <span className="hidden rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.18em] text-blue-700 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-300 sm:inline-flex">
              AI Workspace
            </span>
          </div>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400">
            Grounded document intelligence with citations and Ollama models
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={clearMessages}
          title="Clear chat"
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:border-red-200 hover:bg-red-50 hover:text-red-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:border-red-900 dark:hover:bg-red-950/60 dark:hover:text-red-300"
        >
          <Trash2 size={18} />
        </button>

        <button
          onClick={() => fileRef.current?.click()}
          disabled={upload.isPending}
          className="inline-flex h-10 items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-4 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 transition hover:from-blue-700 hover:to-cyan-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <FileUp size={17} />
          {upload.isPending ? 'Uploading...' : 'Upload document'}
        </button>
        <input ref={fileRef} type="file" className="hidden" accept=".pdf,.docx,.pptx" onChange={handleFile} />

        <button
          onClick={toggleTheme}
          title="Toggle theme"
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400 dark:hover:border-blue-900 dark:hover:bg-blue-950/60 dark:hover:text-blue-300"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}

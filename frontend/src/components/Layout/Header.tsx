import { FileUp, Moon, Sun, Trash2 } from 'lucide-react';
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
    <header className="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
          <span className="text-white font-bold text-sm">D</span>
        </div>
        <h1 className="text-lg font-semibold">DocQA Assistant</h1>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={clearMessages}
          title="Clear chat"
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
        >
          <Trash2 size={18} />
        </button>

        <button
          onClick={() => fileRef.current?.click()}
          disabled={upload.isPending}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50 transition-colors"
        >
          <FileUp size={16} />
          {upload.isPending ? 'Uploading...' : 'Upload'}
        </button>
        <input ref={fileRef} type="file" className="hidden" accept=".pdf,.docx,.pptx" onChange={handleFile} />

        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}

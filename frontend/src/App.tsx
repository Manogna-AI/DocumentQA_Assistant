import { useEffect } from 'react';
import { useAppStore } from '@/stores/appStore';
import Header from '@/components/Layout/Header';
import StatusBar from '@/components/Layout/StatusBar';
import DocumentPanel from '@/components/Documents/DocumentPanel';
import ChatPanel from '@/components/Chat/ChatPanel';
import CitationPanel from '@/components/Citations/CitationPanel';

export default function App() {
  const theme = useAppStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return (
    <div className="h-full overflow-hidden bg-slate-100 text-slate-950 dark:bg-slate-950 dark:text-slate-100">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-32 top-[-18rem] h-[34rem] w-[34rem] rounded-full bg-blue-300/30 blur-3xl dark:bg-blue-600/20" />
        <div className="absolute -right-28 bottom-[-20rem] h-[36rem] w-[36rem] rounded-full bg-cyan-300/25 blur-3xl dark:bg-cyan-500/10" />
      </div>

      <div className="relative mx-auto flex h-full max-w-[1600px] flex-col p-3 sm:p-4 lg:p-6">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[2rem] border border-white/70 bg-white/80 shadow-2xl shadow-slate-200/80 backdrop-blur-xl dark:border-slate-800/80 dark:bg-slate-950/70 dark:shadow-black/30">
          <Header />
          <div className="grid min-h-0 flex-1 grid-cols-1 overflow-hidden lg:grid-cols-[300px_minmax(0,1fr)] xl:grid-cols-[320px_minmax(0,1fr)_360px]">
            <DocumentPanel />
            <ChatPanel />
            <CitationPanel />
          </div>
          <StatusBar />
        </div>
      </div>
    </div>
  );
}

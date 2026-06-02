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
    <div className="h-full flex flex-col">
      <Header />
      <div className="flex-1 grid grid-cols-[280px_1fr_320px] min-h-0">
        <DocumentPanel />
        <ChatPanel />
        <CitationPanel />
      </div>
      <StatusBar />
    </div>
  );
}

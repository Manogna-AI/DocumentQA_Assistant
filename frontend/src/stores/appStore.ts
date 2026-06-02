import { create } from 'zustand';
import { LOG_MESSAGE_PREVIEW_CHARS } from '@/config/frontend.config';
import type { Message, Citation } from '@/types/chat';

interface AppState {
  userId: string;
  selectedDocumentId: string | null;
  theme: 'light' | 'dark';
  messages: Message[];
  citations: Citation[];
  isQuerying: boolean;

  setUserId: (id: string) => void;
  setSelectedDocumentId: (id: string | null) => void;
  toggleTheme: () => void;
  addMessage: (msg: Message) => void;
  updateLastMessage: (content: string, citations?: Citation[]) => void;
  setCitations: (c: Citation[]) => void;
  setIsQuerying: (v: boolean) => void;
  clearMessages: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  userId: 'user_123',
  selectedDocumentId: null,
  theme: (typeof window !== 'undefined' && localStorage.getItem('theme') === 'dark')
    ? 'dark'
    : 'light',
  messages: [],
  citations: [],
  isQuerying: false,

  setUserId: (id) => set({ userId: id }),
  setSelectedDocumentId: (id) => set({ selectedDocumentId: id }),

  toggleTheme: () =>
    set((s) => {
      const next = s.theme === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', next);
      document.documentElement.classList.toggle('dark', next === 'dark');
      return { theme: next };
    }),

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),

  updateLastMessage: (content, citations) =>
    set((s) => {
      const msgs = [...s.messages];
      
      // ✗ Guard: No messages in array
      if (msgs.length === 0) {
        console.warn('[appStore] updateLastMessage: Cannot update — messages array is empty', {
          content: content.substring(0, LOG_MESSAGE_PREVIEW_CHARS) + '...',  // ✓ Use centralized config
          citationCount: citations?.length ?? 0,
        });
        return { messages: msgs };
      }
      
      const lastIdx = msgs.length - 1;
      const last = msgs[lastIdx];
      
      // ✗ Guard: Last message is not assistant (should never happen in normal flow)
      if (!last) {
        console.error('[appStore] updateLastMessage: Last message is undefined (corrupt state)');
        return { messages: msgs };
      }
      
      if (last.role !== 'assistant') {
        console.warn('[appStore] updateLastMessage: Last message is not assistant', {
          actualRole: last.role,
          expectedRole: 'assistant',
        });
        return { messages: msgs };
      }
      
      // ✓ Update: Replace last message with updated content
      msgs[lastIdx] = {
        ...last,
        content,
        citations: citations ?? [],
        isLoading: false,
      };
      
      console.debug('[appStore] updateLastMessage: Updated assistant message', {
        contentLength: content.length,
        citationCount: citations?.length ?? 0,
        timestamp: new Date().toISOString(),
      });
      
      return { messages: msgs };
    }),

  setCitations: (c) => set({ citations: c }),
  setIsQuerying: (v) => set({ isQuerying: v }),
  clearMessages: () => set({ messages: [], citations: [] }),
}));

import { create } from 'zustand';
import { streamSSE } from '../utils/sse';

export type ChatRole = 'system' | 'user' | 'assistant';

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  model: string;
  systemPrompt: string;
  sendMessage: (content: string) => Promise<void>;
  setModel: (model: string) => void;
  setSystemPrompt: (prompt: string) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  model: 'gpt',
  systemPrompt: '',
  async sendMessage(content: string) {
    if (!content.trim()) return;
    const { messages, systemPrompt, model } = get();
    const updatedMessages = [...messages, { role: 'user', content }, { role: 'assistant', content: '' }];
    set({ messages: updatedMessages, isStreaming: true });

    const body = {
      messages: [...messages, { role: 'user', content }],
      model,
      system_prompt: systemPrompt || undefined,
    };

    await streamSSE(
      '/api/chat/stream',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      },
      (chunk) => {
        set((state) => {
          const newMessages = [...state.messages];
          const lastIndex = newMessages.length - 1;
          newMessages[lastIndex] = {
            ...newMessages[lastIndex],
            content: (newMessages[lastIndex]?.content || '') + chunk,
          };
          return { messages: newMessages };
        });
      },
      () => set({ isStreaming: false }),
      () => set({ isStreaming: false })
    );
  },
  setModel(model: string) {
    set({ model });
  },
  setSystemPrompt(prompt: string) {
    set({ systemPrompt: prompt });
  },
  reset() {
    set({ messages: [] });
  },
}));

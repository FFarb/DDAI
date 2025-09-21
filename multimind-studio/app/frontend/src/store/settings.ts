import { create } from 'zustand';

interface SettingsState {
  data: Record<string, string>;
  isSaving: boolean;
  loadSettings: () => Promise<void>;
  updateField: (key: string, value: string) => void;
  saveSettings: () => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  data: {
    OPENAI_API_KEY: '',
    ANTHROPIC_API_KEY: '',
    MISTRAL_API_KEY: '',
    MODEL_NAME: 'gpt-4o-mini',
    WORKSPACE_DIR: './workspace',
    VECTORSTORE_DIR: './vectorstore',
  },
  isSaving: false,
  async loadSettings() {
    const response = await fetch('/api/settings');
    if (!response.ok) return;
    const data = await response.json();
    set({ data: { ...get().data, ...data.settings } });
  },
  updateField(key: string, value: string) {
    set((state) => ({ data: { ...state.data, [key]: value } }));
  },
  async saveSettings() {
    set({ isSaving: true });
    const { data } = get();
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data }),
    });
    set({ isSaving: false });
  },
}));

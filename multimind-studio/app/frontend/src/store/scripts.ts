import { create } from 'zustand';
import { streamSSE } from '../utils/sse';

export interface ScriptItem {
  id: number;
  name: string;
  language: string;
  path: string;
  tags: string[];
  content?: string;
}

interface ScriptsState {
  scripts: ScriptItem[];
  selectedScript?: ScriptItem;
  currentContent: string;
  isLoading: boolean;
  isRunning: boolean;
  runId?: string;
  runLogs: string[];
  artifacts: string[];
  fetchScripts: () => Promise<void>;
  selectScript: (id: number) => Promise<void>;
  updateContent: (content: string) => void;
  saveScript: () => Promise<void>;
  runScript: () => Promise<void>;
  stopRun: () => Promise<void>;
  fetchArtifacts: () => Promise<void>;
}

export const useScriptsStore = create<ScriptsState>((set, get) => ({
  scripts: [],
  selectedScript: undefined,
  currentContent: '',
  isLoading: false,
  isRunning: false,
  runId: undefined,
  runLogs: [],
  artifacts: [],
  async fetchScripts() {
    set({ isLoading: true });
    const response = await fetch('/api/scripts');
    const data = await response.json();
    set({ scripts: data.scripts, isLoading: false });
  },
  async selectScript(id: number) {
    set({ isLoading: true, runLogs: [], artifacts: [] });
    const response = await fetch(`/api/scripts/${id}`);
    if (!response.ok) {
      set({ isLoading: false });
      return;
    }
    const data = await response.json();
    set({ selectedScript: data.script, currentContent: data.script.content || '', isLoading: false });
  },
  updateContent(content: string) {
    set({ currentContent: content });
  },
  async saveScript() {
    const { selectedScript, currentContent } = get();
    if (!selectedScript) return;
    await fetch(`/api/scripts/${selectedScript.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: currentContent }),
    });
  },
  async runScript() {
    const { selectedScript, currentContent } = get();
    if (!selectedScript) return;
    await fetch(`/api/scripts/${selectedScript.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: currentContent }),
    });
    const response = await fetch('/api/scripts/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script_id: selectedScript.id }),
    });
    if (!response.ok) return;
    const data = await response.json();
    const runId = data.run_id;
    set({ runId, isRunning: true, runLogs: [] });

    await streamSSE(
      `/api/scripts/runs/${runId}/stream`,
      {},
      (chunk) => {
        set((state) => {
          let line = chunk;
          try {
            const payload = JSON.parse(chunk);
            if (payload.type === 'stdout' || payload.type === 'stderr') {
              line = `[${payload.type}] ${payload.data}`;
            } else if (payload.type === 'status') {
              line = `[status] ${payload.data}`;
            }
          } catch (error) {
            line = chunk;
          }
          return { runLogs: [...state.runLogs, line] };
        });
      },
      () => set({ isRunning: false }),
      () => set({ isRunning: false })
    );
  },
  async stopRun() {
    const { runId } = get();
    if (!runId) return;
    await fetch('/api/scripts/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id: runId }),
    });
    set({ isRunning: false });
  },
  async fetchArtifacts() {
    const { runId } = get();
    if (!runId) return;
    const response = await fetch(`/api/scripts/runs/${runId}/artifacts`);
    if (!response.ok) return;
    const data = await response.json();
    set({ artifacts: data.artifacts || [] });
  },
}));

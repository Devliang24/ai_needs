import { nanoid } from 'nanoid';
import { create } from 'zustand';
import type { Document, SessionDetail } from '../types';

export const DOCUMENT_HISTORY_STORAGE_KEY = 'document_histories';

export interface AgentResult {
  id: string;
  sender: string;
  stage: string;
  content: unknown;
  payload?: Record<string, unknown>;
  progress: number;
  timestamp: number;
  startedAt?: number;
  needsConfirmation?: boolean;  // 是否需要确认
  confirmed?: boolean;           // 是否已确认
  editable?: boolean;            // 是否可编辑
  durationSeconds?: number | null;
}

export interface DocumentHistoryEntry {
  sessionId: string;
  timestamp: number;
  agentResults: AgentResult[];
}

const loadDocumentHistories = (): Record<string, DocumentHistoryEntry[]> => {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(DOCUMENT_HISTORY_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      return parsed as Record<string, DocumentHistoryEntry[]>;
    }
  } catch (error) {
    console.error('Failed to load document history from localStorage:', error);
  }
  return {};
};

const persistDocumentHistories = (histories: Record<string, DocumentHistoryEntry[]>) => {
  if (typeof window === 'undefined') return;
  try {
    if (Object.keys(histories).length === 0) {
      window.localStorage.removeItem(DOCUMENT_HISTORY_STORAGE_KEY);
    } else {
      window.localStorage.setItem(DOCUMENT_HISTORY_STORAGE_KEY, JSON.stringify(histories));
    }
  } catch (error) {
    console.error('Failed to persist document history to localStorage:', error);
  }
};

export interface SystemMessage {
  id: string;
  content: string;
  timestamp: number;
}

interface AppState {
  documents: Document[];
  session: SessionDetail | null;
  agentResults: AgentResult[];
  systemMessages: SystemMessage[];
  isConnecting: boolean;
  progress: number;
  currentStage: string | null;
  selectedStage: string | null;
  websocket: WebSocket | null;
  analysisRunning: boolean;
  lastActivityTime: number;
  addDocument: (document: Document) => void;
  removeDocument: (documentId: string) => void;
  clearDocuments: () => void;
  setSession: (session: SessionDetail) => void;
  addAgentResult: (result: Omit<AgentResult, 'id' | 'timestamp'>) => void;
  appendAgentResult: (result: Omit<AgentResult, 'id' | 'timestamp'>) => void;
  addSystemMessage: (content: string) => void;
  setConnecting: (value: boolean) => void;
  setProgress: (progress: number, stage: string | null) => void;
  setSelectedStage: (stage: string | null) => void;
  setWebSocket: (ws: WebSocket | null) => void;
  sendConfirmation: (resultId: string, stage: string, payload?: Record<string, unknown>) => void;
  confirmAgentResult: (resultId: string) => void;
  updateAgentResult: (resultId: string, payload: Record<string, unknown>, contentOverride?: string) => void;
  updateActivityTime: () => void;
  clearAnalysisResults: () => void;
  resetAnalysis: () => void;
  reset: () => void;
  documentHistories: Record<string, DocumentHistoryEntry[]>;
  addDocumentHistory: (documentId: string, entry: DocumentHistoryEntry) => void;
  clearDocumentHistory: (documentId: string) => void;
  setAgentResults: (results: AgentResult[]) => void;
  setAnalysisRunning: (value: boolean) => void;
}

const initialDocumentHistories = loadDocumentHistories();

export const useAppStore = create<AppState>((set, get) => ({
  documents: [],
  session: null,
  agentResults: [],
  systemMessages: [],
  isConnecting: false,
  progress: 0,
  currentStage: null,
  selectedStage: 'requirement_analysis',
  websocket: null,
  documentHistories: initialDocumentHistories,
  analysisRunning: false,
  lastActivityTime: 0,
  addDocument: (document) =>
    set((state) => ({
      documents: state.documents.some((d) => d.id === document.id)
        ? state.documents
        : [...state.documents, document]
    })),
  removeDocument: (documentId) =>
    set((state) => {
      const nextDocuments = state.documents.filter((d) => d.id !== documentId);
      const { [documentId]: _removed, ...restHistories } = state.documentHistories;
      persistDocumentHistories(restHistories);
      return {
        documents: nextDocuments,
        documentHistories: restHistories
      };
    }),
  clearDocuments: () =>
    set(() => {
      persistDocumentHistories({});
      return { documents: [], documentHistories: {} };
    }),
  setSession: (session) => set({ session }),
  addAgentResult: (result) =>
    set((state) => {
      const now = Date.now();
      return {
        agentResults: [
          ...state.agentResults,
          {
            ...result,
            id: nanoid(),
            timestamp: now,
            startedAt: now,
            durationSeconds: result.durationSeconds ?? null
          }
        ]
      };
    }),
  appendAgentResult: (result) =>
    set((state) => {
      const results = state.agentResults;
      // 从后往前找最近的同 sender+stage 且未确认的项
      let idx = -1;
      for (let i = results.length - 1; i >= 0; i--) {
        const r = results[i];
        if (r.sender === result.sender && r.stage === result.stage && !r.confirmed) {
          idx = i;
          break;
        }
      }

      const toText = (value: unknown): string => {
        if (value == null) return '';
        if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
        try {
          return JSON.stringify(value);
        } catch {
          return String(value);
        }
      };

      if (idx >= 0) {
        const target = results[idx];
        const prevText = toText(target.content);
        const newText = toText(result.content);
        let mergedContent: string;
        if (!prevText) {
          mergedContent = newText;
        } else if (!newText) {
          mergedContent = prevText;
        } else if (newText === prevText || newText.includes(prevText)) {
          // New content is same or superset -> replace to avoid duplication
          mergedContent = newText;
        } else if (prevText.includes(newText)) {
          // Old content already contains new -> keep old
          mergedContent = prevText;
        } else {
          // Different incremental chunk -> append
          mergedContent = `${prevText}\n${newText}`;
        }

        const now = Date.now();
        const merged = {
          ...target,
          content: mergedContent,
          payload: result.payload ?? target.payload,
          progress: typeof result.progress === 'number' ? result.progress : target.progress,
          // needsConfirmation: 优先使用true值（一旦设为true就保持true）
          needsConfirmation: result.needsConfirmation === true || target.needsConfirmation === true,
          timestamp: now,
          startedAt: target.startedAt ?? target.timestamp,
          durationSeconds: typeof result.durationSeconds === 'number' ? result.durationSeconds : target.durationSeconds ?? null
        } as AgentResult;

        const next = results.slice();
        next[idx] = merged;
        return { agentResults: next };
      }

      // 否则按新消息追加
      const now = Date.now();
      return {
        agentResults: [
          ...results,
          {
            ...result,
            id: nanoid(),
            timestamp: now,
            startedAt: now,
            durationSeconds: result.durationSeconds ?? null
          }
        ]
      };
    }),
  addSystemMessage: (content) =>
    set((state) => ({
      systemMessages: [
        ...state.systemMessages,
        {
          id: nanoid(),
          content,
          timestamp: Date.now()
        }
      ]
    })),
  setConnecting: (value) => set({ isConnecting: value }),
  setProgress: (progress, stage) => set({ progress, currentStage: stage }),
  setSelectedStage: (stage) => set({ selectedStage: stage }),
  setWebSocket: (ws) => set({ websocket: ws }),
  sendConfirmation: (resultId, stage, payload) => {
    const { websocket } = get();
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'confirm_agent',
        stage,
        result_id: resultId,
        payload: payload || null,
        confirmed: true
      };
      websocket.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  },
  confirmAgentResult: (resultId) =>
    set((state) => ({
      agentResults: state.agentResults.map((r) =>
        r.id === resultId ? { ...r, confirmed: true, needsConfirmation: false } : r
      )
    })),
  updateAgentResult: (resultId, payload, contentOverride) =>
    set((state) => ({
      agentResults: state.agentResults.map((r) =>
        r.id === resultId
          ? {
              ...r,
              payload,
              ...(contentOverride !== undefined ? { content: contentOverride } : {}),
              confirmed: true,
              needsConfirmation: false,
              durationSeconds: r.durationSeconds ?? null
            }
          : r
      )
    })),
  updateActivityTime: () => set({ lastActivityTime: Date.now() }),
  clearAnalysisResults: () =>
    set({
      session: null,
      agentResults: [],
      systemMessages: [],
      isConnecting: false,
      websocket: null,
      // 注意：不重置以下状态，保持加载状态和进度
      // - analysisRunning: 保持加载状态
      // - progress: 保持进度显示
      // - currentStage: 保持当前阶段，用于加载判断
      // - selectedStage: 保持选中阶段
    }),
  resetAnalysis: () =>
    set({
      session: null,
      agentResults: [],
      systemMessages: [],
      progress: 0,
      currentStage: null,
      selectedStage: 'requirement_analysis',
      isConnecting: false,
      websocket: null,
      analysisRunning: false
    }),
  reset: () =>
    set(() => {
      persistDocumentHistories({});
      return {
        documents: [],
        session: null,
        agentResults: [],
        systemMessages: [],
        progress: 0,
        currentStage: null,
        selectedStage: 'requirement_analysis',
        isConnecting: false,
        websocket: null,
        documentHistories: {},
        analysisRunning: false
      };
    }),
  addDocumentHistory: (documentId, entry) =>
    set((state) => {
      const existing = state.documentHistories[documentId] ?? [];
      const filtered = existing.filter((item) => item.sessionId !== entry.sessionId);
      const nextEntries = [entry, ...filtered].sort((a, b) => b.timestamp - a.timestamp).slice(0, 10);
      const nextHistories = {
        ...state.documentHistories,
        [documentId]: nextEntries
      };
      persistDocumentHistories(nextHistories);
      return { documentHistories: nextHistories };
    }),
  clearDocumentHistory: (documentId) =>
    set((state) => {
      if (!(documentId in state.documentHistories)) {
        return {};
      }
      const { [documentId]: _removed, ...rest } = state.documentHistories;
      persistDocumentHistories(rest);
      return { documentHistories: rest };
    }),
  setAgentResults: (results) => set({ agentResults: results }),
  setAnalysisRunning: (value) => set({ analysisRunning: value })
}));

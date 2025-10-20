import axios from 'axios';
import type {
  DocumentUploadResponse,
  SessionCreateRequest,
  SessionCreateResponse,
  SessionDetail,
  SessionListResponse,
  SessionResultsResponse
} from '../types';

const baseURL = import.meta.env.VITE_API_URL ?? window.location.origin;

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post<DocumentUploadResponse>('/api/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
}

export async function createSession(payload: SessionCreateRequest): Promise<SessionCreateResponse> {
  const response = await apiClient.post<SessionCreateResponse>('/api/sessions', payload);
  return response.data;
}

export async function fetchSessions(page = 1, status?: string): Promise<SessionListResponse> {
  const params: Record<string, unknown> = { page };
  if (status) params.status = status;
  const response = await apiClient.get<SessionListResponse>('/api/sessions', { params });
  return response.data;
}

export async function fetchSessionDetail(sessionId: string): Promise<SessionDetail> {
  const response = await apiClient.get<SessionDetail>(`/api/sessions/${sessionId}`);
  return response.data;
}

export async function fetchSessionResults(sessionId: string): Promise<SessionResultsResponse> {
  const response = await apiClient.get<SessionResultsResponse>(`/api/sessions/${sessionId}/results`);
  return response.data;
}

export async function exportSessionXmind(sessionId: string, resultVersion?: number): Promise<Blob> {
  const response = await apiClient.post<Blob>(
    `/api/sessions/${sessionId}/exports/xmind`,
    { result_version: resultVersion },
    { responseType: 'blob' }
  );
  return response.data;
}

export async function exportSessionExcel(sessionId: string, resultVersion?: number): Promise<Blob> {
  const response = await apiClient.post<Blob>(
    `/api/sessions/${sessionId}/exports/excel`,
    { result_version: resultVersion },
    { responseType: 'blob' }
  );
  return response.data;
}

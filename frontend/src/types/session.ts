export interface SessionSummary {
  id: string;
  status: string;
  current_stage: string | null;
  progress: number;
  created_at: string;
  expires_at: string | null;
  last_activity_at: string;
}

export interface SessionDetail extends SessionSummary {
  config: Record<string, unknown>;
  documents: import('./document').Document[];
}

export interface SessionListResponse {
  items: SessionSummary[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
  };
}

export interface SessionCreateRequest {
  document_ids: string[];
  config?: Record<string, unknown>;
  created_by?: string | null;
}

export interface SessionCreateResponse {
  session_id: string;
  status: string;
  expires_at: string | null;
}

export interface SessionResultsResponse {
  analysis: Record<string, unknown> | string;
  test_cases: Record<string, unknown>;
  statistics: Record<string, unknown>;
  version: number;
  generated_at: string;
}

export type AnalysisStatus = 'not_started' | 'recognizing' | 'analyzing' | 'completed';

export interface Document {
  id: string;
  original_name: string;
  storage_path: string;
  checksum: string;
  size: number;
  status: string;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
  // 分析状态相关字段
  analysis_status?: AnalysisStatus;
  analysis_progress?: number;
  session_id?: string;
}

export interface DocumentUploadResponse {
  document: Document;
  is_duplicate: boolean;
}

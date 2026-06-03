export interface DocumentInfo {
  document_id: string;
  document_name: string;
  file_type: string;
  status: 'processing' | 'indexed' | 'failed';
  chunk_count: number;
  created_at: string;
  updated_at: string;
  error?: string;
}

export interface UploadResponse {
  document_id: string;
  document_name: string;
  file_type: string;
  chunk_count: number;
  status: string;
  message: string;
}

export interface DocumentListResponse {
  user_id: string;
  documents: DocumentInfo[];
}

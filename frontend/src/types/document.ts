export interface DocumentInfo {
  document_id: string;
  document_name: string;
  file_type: string;
  status: 'processing' | 'indexed' | 'failed';
  chunk_count: number;
  uploaded_at: string;
  error?: string;
}

export interface UploadResponse {
  document_id: string;
  document_name: string;
  file_type: string;
  chunk_count: number;
  status: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
}

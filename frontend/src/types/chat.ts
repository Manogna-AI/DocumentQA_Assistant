export interface Citation {
  document_id: string;
  document_name: string;
  chunk_id: string;
  page_number: number | null;
  slide_number: number | null;
  section_title: string | null;
  snippet: string;
  score: number | null;
}

export interface QueryRequest {
  user_id: string;
  message: string;
  document_id?: string;
}

export interface QueryResponse {
  answer: string;
  citations?: Citation[];
  metadata?: {
    status: string;
    intent: string;
    retrieved_count?: number;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
  isLoading?: boolean;
}

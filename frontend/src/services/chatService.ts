import api from './api';
import type { QueryRequest, QueryResponse } from '@/types/chat';

export async function sendQuery(request: QueryRequest): Promise<QueryResponse> {
  const { data } = await api.post<QueryResponse>('/chat/query', request);
  return data;
}

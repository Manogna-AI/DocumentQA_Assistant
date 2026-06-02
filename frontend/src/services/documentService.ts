import api from './api';
import { UPLOAD_TIMEOUT_MS } from '@/config/frontend.config';
import type { DocumentListResponse, UploadResponse } from '@/types/document';

export async function uploadDocument(file: File, userId: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);

  const { data } = await api.post<UploadResponse>('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: UPLOAD_TIMEOUT_MS,  // ✓ Use centralized config (5 min for large files)
  });
  return data;
}

export async function listDocuments(userId: string): Promise<DocumentListResponse> {
  const { data } = await api.get<DocumentListResponse>('/documents/list', {
    params: { user_id: userId },
  });
  return data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await api.delete(`/documents/${documentId}`);
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { uploadDocument, listDocuments, deleteDocument } from '@/services/documentService';
import { useAppStore } from '@/stores/appStore';
import { DOCUMENT_POLL_INTERVAL_MS } from '@/config/frontend.config';

// ✓ Helper: Extract error message from various error types
function getErrorMessage(err: unknown, defaultMsg: string): string {
  if (!err) return defaultMsg;
  
  // Handle axios error with response data
  if (typeof err === 'object' && 'response' in err) {
    const axiosErr = err as any;
    if (axiosErr.response?.data?.detail) {
      return axiosErr.response.data.detail;
    }
    if (axiosErr.response?.data?.message) {
      return axiosErr.response.data.message;
    }
  }
  
  // Handle standard error
  if (err instanceof Error) {
    return err.message;
  }
  
  // Fallback to default
  return defaultMsg;
}

export function useDocumentList() {
  const userId = useAppStore((s) => s.userId);
  return useQuery({
    queryKey: ['documents', userId],
    queryFn: () => listDocuments(userId),
    refetchInterval: DOCUMENT_POLL_INTERVAL_MS,  // ✓ Use centralized config (poll for status changes)
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  const userId = useAppStore((s) => s.userId);

  return useMutation({
    mutationFn: (file: File) => uploadDocument(file, userId),
    onSuccess: (data) => {
      toast.success(`Uploaded "${data.document_name}" — ${data.chunk_count} chunks indexed`);
      
      // ✓ Log successful upload
      console.debug('[useUploadDocument] Upload successful', {
        documentName: data.document_name,
        documentId: data.document_id,
        chunkCount: data.chunk_count,
        timestamp: new Date().toISOString(),
      });
      
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      // ✓ Extract detailed error message
      const errorMsg = getErrorMessage(err, 'Upload failed');
      
      // ✓ Log error with context
      console.error('[useUploadDocument] Upload failed', {
        errorMessage: errorMsg,
        errorStatus: err?.response?.status,
        userId,
        timestamp: new Date().toISOString(),
      });
      
      toast.error(errorMsg);
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      toast.success('Document deleted');
      
      // ✓ Log successful deletion
      console.debug('[useDeleteDocument] Document deleted successfully', {
        timestamp: new Date().toISOString(),
      });
      
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      // ✓ Extract detailed error message (NEW)
      const errorMsg = getErrorMessage(err, 'Failed to delete document');
      
      // ✓ Log error with context (NEW)
      console.error('[useDeleteDocument] Delete failed', {
        errorMessage: errorMsg,
        errorStatus: err?.response?.status,
        timestamp: new Date().toISOString(),
      });
      
      toast.error(errorMsg);
    },
  });
}

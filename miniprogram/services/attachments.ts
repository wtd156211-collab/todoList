import { request, type ApiResult } from './api';

export interface UploadPolicyRequest {
  filename: string;
  mimeType: 'application/pdf' | 'image/jpeg' | 'image/png';
  sizeBytes: number;
}

export interface UploadPolicy {
  attachmentId: string;
  objectKey: string;
  host: string;
  formData: Record<string, string>;
}

export function requestUploadPolicy(
  accessToken: string,
  taskId: string,
  payload: UploadPolicyRequest
): Promise<ApiResult<UploadPolicy>> {
  return request<UploadPolicy>(`/tasks/${taskId}/attachments/upload-policy`, {
    accessToken,
    method: 'POST',
    data: payload
  });
}

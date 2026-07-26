import { API_BASE_URL } from '../config';

export type ApiErrorCode =
  | 'AUTHENTICATION_FAILED'
  | 'CONFLICT'
  | 'FORBIDDEN'
  | 'INTERNAL_ERROR'
  | 'NOT_FOUND'
  | 'UPLOAD_REJECTED'
  | 'VALIDATION_ERROR';

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; code: ApiErrorCode; message: string };

export interface RequestOptions {
  accessToken?: string;
  data?: unknown;
  method?: 'DELETE' | 'GET' | 'PATCH' | 'POST';
}

export interface RequestAdapter {
  request(options: {
    url: string;
    method: string;
    data?: unknown;
    header: Record<string, string>;
  }): Promise<{ statusCode: number; data: unknown }>;
}

let requestAdapter: RequestAdapter | undefined;

export function setRequestAdapter(adapter: RequestAdapter | undefined): void {
  requestAdapter = adapter;
}

function getDefaultAdapter(): RequestAdapter {
  return {
    request(options) {
      return new Promise((resolve, reject) => {
        wx.request({
          ...options,
          success: resolve,
          fail: reject
        });
      });
    }
  };
}

function isErrorPayload(data: unknown): data is { code: ApiErrorCode; message: string } {
  return Boolean(
    data &&
      typeof data === 'object' &&
      typeof (data as { code?: unknown }).code === 'string' &&
      typeof (data as { message?: unknown }).message === 'string'
  );
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<ApiResult<T>> {
  const header: Record<string, string> = { 'content-type': 'application/json' };
  if (options.accessToken) {
    header.Authorization = `Bearer ${options.accessToken}`;
  }

  try {
    const response = await (requestAdapter ?? getDefaultAdapter()).request({
      url: `${API_BASE_URL}${path}`,
      method: options.method ?? 'GET',
      data: options.data,
      header
    });
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return { ok: true, data: response.data as T };
    }
    if (isErrorPayload(response.data)) {
      return { ok: false, code: response.data.code, message: response.data.message };
    }
    return { ok: false, code: 'INTERNAL_ERROR', message: '服务暂时不可用' };
  } catch {
    return { ok: false, code: 'INTERNAL_ERROR', message: '网络连接失败，请稍后重试' };
  }
}

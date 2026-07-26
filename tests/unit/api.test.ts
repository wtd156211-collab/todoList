import { request, setRequestAdapter, type RequestAdapter } from '../../miniprogram/services/api';
import { afterEach, expect, it } from 'vitest';

afterEach(() => setRequestAdapter(undefined));

it('sends the bearer token and returns a successful API payload', async () => {
  let receivedHeaders: Record<string, string> | undefined;
  const adapter: RequestAdapter = {
    async request(options) {
      receivedHeaders = options.header;
      return { statusCode: 200, data: { items: [] } };
    }
  };
  setRequestAdapter(adapter);

  await expect(request<{ items: unknown[] }>('/tasks', { accessToken: 'access-token' })).resolves.toEqual({
    ok: true,
    data: { items: [] }
  });
  expect(receivedHeaders?.Authorization).toBe('Bearer access-token');
});

it('converts a server error into a stable API result', async () => {
  const adapter: RequestAdapter = {
    async request() {
      return { statusCode: 404, data: { code: 'NOT_FOUND', message: '任务不存在' } };
    }
  };
  setRequestAdapter(adapter);

  await expect(request('/tasks/missing')).resolves.toEqual({
    ok: false,
    code: 'NOT_FOUND',
    message: '任务不存在'
  });
});

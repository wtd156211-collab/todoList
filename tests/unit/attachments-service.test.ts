import { requestUploadPolicy } from '../../miniprogram/services/attachments';
import { setRequestAdapter, type RequestAdapter } from '../../miniprogram/services/api';
import { afterEach, expect, it } from 'vitest';

afterEach(() => setRequestAdapter(undefined));

it('requests a private upload policy for a task attachment', async () => {
  const adapter: RequestAdapter = {
    async request(options) {
      expect(options.method).toBe('POST');
      expect(options.data).toEqual({ filename: 'receipt.pdf', mimeType: 'application/pdf', sizeBytes: 1024 });
      return {
        statusCode: 200,
        data: {
          attachmentId: 'attachment-1',
          objectKey: 'flowlist/user/task/file.pdf',
          host: 'https://flowlist.oss-cn-beijing.aliyuncs.com',
          formData: { key: 'flowlist/user/task/file.pdf' }
        }
      };
    }
  };
  setRequestAdapter(adapter);

  await expect(
    requestUploadPolicy('access-token', 'task-1', {
      filename: 'receipt.pdf',
      mimeType: 'application/pdf',
      sizeBytes: 1024
    })
  ).resolves.toEqual({
    ok: true,
    data: {
      attachmentId: 'attachment-1',
      objectKey: 'flowlist/user/task/file.pdf',
      host: 'https://flowlist.oss-cn-beijing.aliyuncs.com',
      formData: { key: 'flowlist/user/task/file.pdf' }
    }
  });
});

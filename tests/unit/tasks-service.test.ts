import { createTask, listTasks } from '../../miniprogram/services/tasks';
import { setRequestAdapter, type RequestAdapter } from '../../miniprogram/services/api';
import { afterEach, expect, it } from 'vitest';

afterEach(() => setRequestAdapter(undefined));

it('lists the current user tasks with the access token', async () => {
  const adapter: RequestAdapter = {
    async request(options) {
      expect(options.method).toBe('GET');
      expect(options.header.Authorization).toBe('Bearer access-token');
      return {
        statusCode: 200,
        data: { items: [{ id: 'task-1', title: '整理项目计划', note: '', priority: 'medium', status: 'todo', version: 1 }] }
      };
    }
  };
  setRequestAdapter(adapter);

  await expect(listTasks('access-token')).resolves.toEqual({
    ok: true,
    data: { items: [{ id: 'task-1', title: '整理项目计划', note: '', priority: 'medium', status: 'todo', version: 1 }] }
  });
});

it('creates a task with the API task input shape', async () => {
  const adapter: RequestAdapter = {
    async request(options) {
      expect(options.method).toBe('POST');
      expect(options.data).toEqual({ title: '整理项目计划', note: '', priority: 'high' });
      return {
        statusCode: 201,
        data: { id: 'task-2', title: '整理项目计划', note: '', priority: 'high', status: 'todo', version: 1 }
      };
    }
  };
  setRequestAdapter(adapter);

  await expect(createTask('access-token', { title: '整理项目计划', note: '', priority: 'high' })).resolves.toEqual({
    ok: true,
    data: { id: 'task-2', title: '整理项目计划', note: '', priority: 'high', status: 'todo', version: 1 }
  });
});

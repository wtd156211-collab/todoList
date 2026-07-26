import { TasksStore, type TaskGateway } from '../../miniprogram/stores/tasks';
import { expect, it } from 'vitest';

it('refresh replaces the task list returned by its gateway', async () => {
  const gateway: TaskGateway = {
    async create() {
      throw new Error('not used');
    },
    async list() {
      return {
        ok: true,
        data: {
          items: [{ id: 'task-1', title: '整理项目计划', note: '', priority: 'medium', status: 'todo', version: 1 }]
        }
      };
    }
  };
  const store = new TasksStore(gateway, () => 'access-token');

  await store.refresh();

  expect(store.items.map((task) => task.id)).toEqual(['task-1']);
  expect(store.loading).toBe(false);
});

it('create prepends a newly created task to the current list', async () => {
  const gateway: TaskGateway = {
    async create() {
      return {
        ok: true,
        data: { id: 'task-2', title: '完成小程序', note: '', priority: 'high', status: 'todo', version: 1 }
      };
    },
    async list() {
      throw new Error('not used');
    }
  };
  const store = new TasksStore(gateway, () => 'access-token');

  const result = await store.create({ title: '完成小程序', note: '', priority: 'high' });

  expect(result.ok).toBe(true);
  expect(store.items.map((task) => task.id)).toEqual(['task-2']);
});

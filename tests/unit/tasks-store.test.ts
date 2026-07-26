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

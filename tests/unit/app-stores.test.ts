import { createAppStores } from '../../miniprogram/stores/app';
import type { TaskGateway } from '../../miniprogram/stores/tasks';
import type { SessionStorage } from '../../miniprogram/utils/storage';
import { expect, it } from 'vitest';

function createStorage(): SessionStorage {
  const values = new Map<string, unknown>();
  return {
    get: (key) => values.get(key),
    remove: (key) => values.delete(key),
    set: (key, value) => values.set(key, value)
  };
}

it('uses the current session token when refreshing application tasks', async () => {
  let receivedToken = '';
  const gateway: TaskGateway = {
    async create() {
      throw new Error('not used');
    },
    async list(accessToken) {
      receivedToken = accessToken;
      return { ok: true, data: { items: [] } };
    }
  };
  const stores = createAppStores(createStorage(), gateway);
  stores.session.setTokens({ accessToken: 'access-token', refreshToken: 'refresh-token' });

  await stores.tasks.refresh();

  expect(receivedToken).toBe('access-token');
});

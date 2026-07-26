import { SessionStore } from '../../miniprogram/stores/session';
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

it('restores persisted tokens into observable session state', () => {
  const store = new SessionStore(createStorage());

  store.setTokens({ accessToken: 'access', refreshToken: 'refresh' });

  expect(store.accessToken).toBe('access');
  expect(store.isAuthenticated).toBe(true);

  store.clear();
  expect(store.isAuthenticated).toBe(false);
});

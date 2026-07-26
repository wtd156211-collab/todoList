import { clearSession, loadSession, saveSession, type SessionStorage } from '../../miniprogram/utils/storage';
import { expect, it } from 'vitest';

function createStorage(): SessionStorage {
  const values = new Map<string, unknown>();
  return {
    get(key) {
      return values.get(key);
    },
    remove(key) {
      values.delete(key);
    },
    set(key, value) {
      values.set(key, value);
    }
  };
}

it('persists and clears access tokens together', () => {
  const storage = createStorage();

  saveSession(storage, { accessToken: 'access', refreshToken: 'refresh' });
  expect(loadSession(storage)).toEqual({ accessToken: 'access', refreshToken: 'refresh' });

  clearSession(storage);
  expect(loadSession(storage)).toBeNull();
});

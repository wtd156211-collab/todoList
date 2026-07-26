export interface SessionTokens {
  accessToken: string;
  refreshToken: string;
}

export interface SessionStorage {
  get(key: string): unknown;
  remove(key: string): void;
  set(key: string, value: unknown): void;
}

const SESSION_KEY = 'flowlist.session';

export function saveSession(storage: SessionStorage, tokens: SessionTokens): void {
  storage.set(SESSION_KEY, tokens);
}

export function loadSession(storage: SessionStorage): SessionTokens | null {
  const value = storage.get(SESSION_KEY);
  if (
    value &&
    typeof value === 'object' &&
    typeof (value as SessionTokens).accessToken === 'string' &&
    typeof (value as SessionTokens).refreshToken === 'string'
  ) {
    return value as SessionTokens;
  }
  return null;
}

export function clearSession(storage: SessionStorage): void {
  storage.remove(SESSION_KEY);
}

import { makeAutoObservable } from 'mobx-miniprogram';

import {
  clearSession,
  loadSession,
  saveSession,
  type SessionStorage,
  type SessionTokens
} from '../utils/storage';

export class SessionStore {
  accessToken = '';
  refreshToken = '';

  constructor(private readonly storage: SessionStorage) {
    makeAutoObservable(this);
    this.restore();
  }

  get isAuthenticated(): boolean {
    return this.accessToken.length > 0;
  }

  setTokens(tokens: SessionTokens): void {
    this.accessToken = tokens.accessToken;
    this.refreshToken = tokens.refreshToken;
    saveSession(this.storage, tokens);
  }

  clear(): void {
    this.accessToken = '';
    this.refreshToken = '';
    clearSession(this.storage);
  }

  private restore(): void {
    const tokens = loadSession(this.storage);
    if (tokens) {
      this.accessToken = tokens.accessToken;
      this.refreshToken = tokens.refreshToken;
    }
  }
}

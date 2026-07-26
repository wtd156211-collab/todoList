import { ensureSession, type SessionController } from '../../miniprogram/services/session';
import { expect, it } from 'vitest';

it('logs in and persists tokens when no valid session exists', async () => {
  const received: string[] = [];
  const session: SessionController = {
    isAuthenticated: false,
    setTokens(tokens) {
      received.push(tokens.accessToken, tokens.refreshToken);
    }
  };

  const result = await ensureSession(session, async () => ({
    ok: true,
    data: {
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      user: { id: 'user-1', openid: 'openid-1' }
    }
  }));

  expect(result).toEqual({ ok: true, data: undefined });
  expect(received).toEqual(['access-token', 'refresh-token']);
});

import { wechatLogin, type AuthSession } from './auth';
import type { ApiResult } from './api';
import type { SessionTokens } from '../utils/storage';

export interface SessionController {
  isAuthenticated: boolean;
  setTokens(tokens: SessionTokens): void;
}

export type LoginAction = () => Promise<ApiResult<AuthSession>>;

export async function ensureSession(
  session: SessionController,
  login: LoginAction = wechatLogin
): Promise<ApiResult<void>> {
  if (session.isAuthenticated) {
    return { ok: true, data: undefined };
  }

  const result = await login();
  if (!result.ok) {
    return result;
  }

  session.setTokens(result.data);
  return { ok: true, data: undefined };
}

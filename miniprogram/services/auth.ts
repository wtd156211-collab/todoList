import { request, type ApiResult } from './api';

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    openid: string;
  };
}

export interface LoginAdapter {
  login(): Promise<{ code?: string }>;
}

let loginAdapter: LoginAdapter | undefined;

export function setLoginAdapter(adapter: LoginAdapter | undefined): void {
  loginAdapter = adapter;
}

function getDefaultLoginAdapter(): LoginAdapter {
  return {
    login() {
      return new Promise((resolve, reject) => {
        wx.login({ success: resolve, fail: reject });
      });
    }
  };
}

export async function wechatLogin(): Promise<ApiResult<AuthSession>> {
  try {
    const { code } = await (loginAdapter ?? getDefaultLoginAdapter()).login();
    if (!code) {
      return { ok: false, code: 'AUTHENTICATION_FAILED', message: '微信登录凭证获取失败' };
    }
    return request<AuthSession>('/auth/wechat-login', { method: 'POST', data: { code } });
  } catch {
    return { ok: false, code: 'AUTHENTICATION_FAILED', message: '微信登录暂不可用，请稍后重试' };
  }
}

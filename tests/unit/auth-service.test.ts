import { setLoginAdapter, wechatLogin, type LoginAdapter } from '../../miniprogram/services/auth';
import { setRequestAdapter, type RequestAdapter } from '../../miniprogram/services/api';
import { afterEach, expect, it } from 'vitest';

afterEach(() => {
  setLoginAdapter(undefined);
  setRequestAdapter(undefined);
});

it('exchanges a WeChat login code for Flowlist tokens', async () => {
  const loginAdapter: LoginAdapter = {
    async login() {
      return { code: 'wx-code' };
    }
  };
  const requestAdapter: RequestAdapter = {
    async request(options) {
      expect(options.method).toBe('POST');
      expect(options.data).toEqual({ code: 'wx-code' });
      return {
        statusCode: 200,
        data: {
          accessToken: 'access-token',
          refreshToken: 'refresh-token',
          user: { id: 'user-1', openid: 'openid-1' }
        }
      };
    }
  };
  setLoginAdapter(loginAdapter);
  setRequestAdapter(requestAdapter);

  await expect(wechatLogin()).resolves.toEqual({
    ok: true,
    data: {
      accessToken: 'access-token',
      refreshToken: 'refresh-token',
      user: { id: 'user-1', openid: 'openid-1' }
    }
  });
});

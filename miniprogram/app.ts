import { ensureSession } from './services/session';
import { createAppStores, type AppStores } from './stores/app';

export interface FlowlistApp {
  globalData: {
    stores: AppStores;
  };
}

const stores = createAppStores({
  get: (key) => wx.getStorageSync(key),
  remove: (key) => wx.removeStorageSync(key),
  set: (key, value) => wx.setStorageSync(key, value)
});

App({
  globalData: { stores },
  async onLaunch() {
    await ensureSession(stores.session);
  }
});

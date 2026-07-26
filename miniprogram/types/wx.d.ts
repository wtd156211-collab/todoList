declare const wx: {
  request(options: {
    url: string;
    method?: string;
    data?: unknown;
    header?: Record<string, string>;
    success(response: { statusCode: number; data: unknown }): void;
    fail(error: unknown): void;
  }): void;
  login(options: {
    success(response: { code?: string }): void;
    fail(error: unknown): void;
  }): void;
  navigateTo(options: { url: string }): void;
  navigateBack(): void;
  getStorageSync(key: string): unknown;
  removeStorageSync(key: string): void;
  setStorageSync(key: string, value: unknown): void;
  showToast(options: { title: string; icon?: 'none' | 'success' }): void;
};

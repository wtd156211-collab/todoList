declare const wx: {
  request(options: {
    url: string;
    method?: string;
    data?: unknown;
    header?: Record<string, string>;
    success(response: { statusCode: number; data: unknown }): void;
    fail(error: unknown): void;
  }): void;
};

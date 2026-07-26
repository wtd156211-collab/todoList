export function toUserMessage(code: string): string {
  const messages: Record<string, string> = {
    AUTHENTICATION_FAILED: '登录已失效，请稍后重试',
    CONFLICT: '任务已在其他设备修改，请刷新后重试',
    FORBIDDEN: '无权执行此操作',
    INTERNAL_ERROR: '服务暂时不可用，请稍后重试',
    NOT_FOUND: '内容不存在或已被删除',
    UPLOAD_REJECTED: '仅支持 10MB 以内的图片或 PDF',
    VALIDATION_ERROR: '请检查填写内容'
  };

  return messages[code] ?? messages.INTERNAL_ERROR;
}

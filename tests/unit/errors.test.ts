import { toUserMessage } from '../../miniprogram/utils/errors';
import { expect, it } from 'vitest';

it('maps a missing task to clear Chinese copy', () => {
  expect(toUserMessage('NOT_FOUND')).toBe('内容不存在或已被删除');
});

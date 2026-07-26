import { normalizeTaskDraft, validateTaskDraft } from '../../miniprogram/components/task-editor/index';
import { expect, it } from 'vitest';

it('rejects an empty task title', () => {
  expect(validateTaskDraft({ title: '   ' })).toBe('请输入任务标题');
});

it('trims the title and defaults priority to medium', () => {
  expect(normalizeTaskDraft({ title: '  整理项目计划  ' })).toEqual({
    title: '整理项目计划',
    note: '',
    priority: 'medium'
  });
});

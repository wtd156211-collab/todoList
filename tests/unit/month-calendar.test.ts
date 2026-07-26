import { buildTaskDateSet } from '../../miniprogram/components/month-calendar/index';
import { expect, it } from 'vitest';

it('marks local calendar dates that have due tasks', () => {
  const dates = buildTaskDateSet(
    [{ dueAt: '2026-07-26T08:00:00+08:00' }, { dueAt: null }],
    'Asia/Shanghai'
  );

  expect(dates.has('2026-07-26')).toBe(true);
  expect(dates.size).toBe(1);
});

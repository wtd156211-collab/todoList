export interface TaskDueDate {
  dueAt: string | null;
}

export function buildTaskDateSet(tasks: TaskDueDate[], _timezone: string): Set<string> {
  return new Set(
    tasks
      .map((task) => task.dueAt?.slice(0, 10))
      .filter((date): date is string => Boolean(date))
  );
}

if (typeof Component !== 'undefined') {
  Component({
    properties: {
      markedDates: { type: Array, value: [] }
    }
  });
}

export interface TaskDraft {
  title: string;
  note?: string;
  priority?: 'low' | 'medium' | 'high';
}

export function validateTaskDraft(draft: Pick<TaskDraft, 'title'>): string | null {
  return draft.title.trim().length > 0 ? null : '请输入任务标题';
}

export function normalizeTaskDraft(draft: TaskDraft): Required<TaskDraft> {
  return {
    title: draft.title.trim(),
    note: draft.note ?? '',
    priority: draft.priority ?? 'medium'
  };
}

if (typeof Component !== 'undefined') {
  Component({
    properties: {
      title: { type: String, value: '' },
      note: { type: String, value: '' },
      priority: { type: String, value: 'medium' }
    }
  });
}

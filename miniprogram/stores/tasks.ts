import { makeAutoObservable } from 'mobx-miniprogram';

import type { ApiResult } from '../services/api';
import type { Task, TaskInput, TaskListResponse } from '../services/tasks';

export interface TaskGateway {
  create(accessToken: string, input: TaskInput): Promise<ApiResult<Task>>;
  list(accessToken: string): Promise<ApiResult<TaskListResponse>>;
}

export class TasksStore {
  items: Task[] = [];
  loading = false;

  constructor(
    private readonly gateway: TaskGateway,
    private readonly getAccessToken: () => string
  ) {
    makeAutoObservable(this);
  }

  async refresh(): Promise<void> {
    this.loading = true;
    try {
      const result = await this.gateway.list(this.getAccessToken());
      if (result.ok) {
        this.items = result.data.items;
      }
    } finally {
      this.loading = false;
    }
  }
}

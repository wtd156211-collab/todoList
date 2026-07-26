import { request, type ApiResult } from './api';

export type TaskPriority = 'low' | 'medium' | 'high';

export interface TaskInput {
  title: string;
  note: string;
  priority: TaskPriority;
}

export interface Task {
  id: string;
  title: string;
  note: string;
  priority: TaskPriority;
  status: 'todo' | 'completed';
  version: number;
}

export interface TaskListResponse {
  items: Task[];
}

export function listTasks(accessToken: string): Promise<ApiResult<TaskListResponse>> {
  return request<TaskListResponse>('/tasks', { accessToken });
}

export function createTask(accessToken: string, input: TaskInput): Promise<ApiResult<Task>> {
  return request<Task>('/tasks', { accessToken, method: 'POST', data: input });
}

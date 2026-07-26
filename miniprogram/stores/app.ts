import { createTask, listTasks } from '../services/tasks';
import type { SessionStorage } from '../utils/storage';
import { SessionStore } from './session';
import { TasksStore, type TaskGateway } from './tasks';

export interface AppStores {
  session: SessionStore;
  tasks: TasksStore;
}

const defaultTaskGateway: TaskGateway = {
  create: createTask,
  list: listTasks
};

export function createAppStores(
  storage: SessionStorage,
  gateway: TaskGateway = defaultTaskGateway
): AppStores {
  const session = new SessionStore(storage);
  return {
    session,
    tasks: new TasksStore(gateway, () => session.accessToken)
  };
}

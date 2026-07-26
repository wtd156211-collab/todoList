# Flowlist WeChat Mini Program MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and release a Chinese-first, private personal-task-management WeChat Mini Program with task CRUD, calendar, attachments, in-app notifications, and opt-in WeChat subscription-message reminders.

**Architecture:** Use a native TypeScript WeChat Mini Program for all UI, with a small service layer that calls CloudBase functions. Cloud functions are the only code allowed to read or change business collections; they derive the current user from the trusted WeChat context, enforce ownership, and own reminder delivery. A five-minute scheduled function atomically claims due reminders, writes an in-app notification, and then sends the approved subscription-message template.

**Tech Stack:** Native WeChat Mini Program (TypeScript, WXML, WXSS), CloudBase, `wx-server-sdk`, MobX Mini Program, Zod, Day.js with UTC/timezone plugins, Vitest, `miniprogram-automator`, WeChat Developer Tools, GitHub Actions.

## Global Constraints

- Target only WeChat Mini Program. Do not add H5, native App, email/password login, Google login, or Apple login.
- Scope is private personal task management. Do not add sharing, invitations, comments, mentions, or roles.
- UI copy is Simplified Chinese. Preserve the Flowlist visual hierarchy from `Flowlist_Wireframes.pdf`.
- A task title is required. Note, due date, reminder, subtasks, and attachments are optional.
- Priority values are exactly `low`, `medium`, and `high`; new tasks default to `medium`.
- Ship built-in `Work` and `Personal` categories. Users can add, rename, and recolor their own categories.
- Allow reminder offsets of `at_due`, `10m`, `30m`, `1h`, and `1d`; reminder is off by default.
- Support image and PDF attachments only; maximum 10 MB per file and five files per task.
- Store timestamps as UTC epoch milliseconds; store an IANA timezone with every dated task. The initial timezone is `Asia/Shanghai`.
- A user must actively grant the approved subscription-message template when saving a task with an external reminder. Rejection must not block saving the task.
- Subscription-message template availability, Mini Program category, and app-review requirements must be confirmed in the WeChat Public Platform before reminder work begins.
- Never send `openid`, `session_key`, AppSecret, or CloudBase administrator credentials to the Mini Program client or logs.
- This folder is not currently a Git repository. Task 1 initializes it before any implementation commits.

---

## Audit Summary and Scope Decision

The existing workspace contains design assets and planning documents, but no application source tree or Git repository. The previous plan correctly selected a native Mini Program plus CloudBase, but it was an architectural document rather than an execution plan: it did not lock down file ownership, function contracts, test commands, or commit boundaries.

This plan covers Mini Program UI, CloudBase business functions, and reminder delivery in one document because they form a single user-visible MVP and cannot be independently released. The subscription-message prerequisite is deliberately separated as an early gate: if the approved template is unavailable, Tasks 1 through 8 remain shippable, while Task 9 is disabled and the product copy must only promise in-app reminders.

| Requirement from the approved scope | Implementing tasks |
| --- | --- |
| WeChat identity and private data | 1, 3, 4 |
| Task create, edit, complete, delete, search, and filter | 2, 4, 5, 7 |
| Categories, subtasks, and attachments | 3, 5, 8 |
| Monthly calendar | 6, 8 |
| In-app notifications and subscription reminders | 6, 9 |
| Profile and settings | 3, 10 |
| Testing, privacy, review, and release | 1, 9, 10, 11 |

## Planned File Structure

```text
.
├── miniprogram/
│   ├── app.ts
│   ├── app.json
│   ├── app.wxss
│   ├── pages/
│   │   ├── welcome/index.{ts,wxml,wxss,json}
│   │   ├── home/index.{ts,wxml,wxss,json}
│   │   ├── task-form/index.{ts,wxml,wxss,json}
│   │   ├── task-detail/index.{ts,wxml,wxss,json}
│   │   ├── calendar/index.{ts,wxml,wxss,json}
│   │   ├── notifications/index.{ts,wxml,wxss,json}
│   │   ├── profile/index.{ts,wxml,wxss,json}
│   │   └── settings/categories/index.{ts,wxml,wxss,json}
│   ├── components/
│   │   ├── task-card/
│   │   ├── task-editor/
│   │   ├── month-calendar/
│   │   ├── bottom-tab-bar/
│   │   └── empty-state/
│   ├── services/
│   │   ├── cloud.ts
│   │   ├── tasks.ts
│   │   ├── categories.ts
│   │   ├── notifications.ts
│   │   ├── reminders.ts
│   │   └── upload.ts
│   ├── stores/
│   │   ├── session.ts
│   │   └── task-filter.ts
│   └── utils/
│       ├── date.ts
│       ├── errors.ts
│       └── subscription.ts
├── shared/
│   ├── domain.ts
│   ├── schemas.ts
│   ├── contracts.ts
│   └── reminder.ts
├── cloudfunctions/
│   ├── _shared/db.ts
│   ├── bootstrap-user/
│   ├── categories/
│   ├── tasks/
│   ├── notifications/
│   ├── task-files/
│   └── send-due-reminders/
├── tests/
│   ├── unit/
│   ├── cloudfunctions/
│   └── e2e/
├── docs/
│   ├── privacy-data-inventory.md
│   ├── release-checklist.md
│   └── superpowers/plans/
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── project.config.json
└── cloudbaserc.json
```

`shared/` is the single source of truth for domain types, validation, function payloads, reminder state, and error codes. Mini Program page code must call a `miniprogram/services/` function instead of invoking cloud functions directly. Cloud-function handlers must import shared validation and query only by the OpenID obtained from `cloud.getWXContext()`.

## Shared Interfaces

All later tasks use these exact names and field names.

```ts
// shared/domain.ts
export type TaskStatus = 'todo' | 'completed';
export type TaskPriority = 'low' | 'medium' | 'high';
export type ReminderOffset = 'at_due' | '10m' | '30m' | '1h' | '1d';
export type ReminderStatus = 'off' | 'pending' | 'skipped' | 'sent' | 'failed';

export interface Category {
  id: string;
  name: string;
  color: string;
  isSystem: boolean;
  sortOrder: number;
}

export interface Subtask {
  id: string;
  title: string;
  completed: boolean;
  sortOrder: number;
}

export interface TaskAttachment {
  fileId: string;
  name: string;
  mimeType: 'image/jpeg' | 'image/png' | 'application/pdf';
  sizeBytes: number;
}

export interface Reminder {
  enabled: boolean;
  offset: ReminderOffset;
  triggerAtMs: number | null;
  status: ReminderStatus;
  templateId: string | null;
  subscriptionGrantedAtMs: number | null;
}

export interface TaskInput {
  id?: string;
  title: string;
  note: string;
  categoryId: string | null;
  priority: TaskPriority;
  dueAtMs: number | null;
  timezone: string;
  reminder: Reminder;
  subtasks: Subtask[];
  attachments: TaskAttachment[];
}

export interface Task extends TaskInput {
  id: string;
  status: TaskStatus;
  completedAtMs: number | null;
  createdAtMs: number;
  updatedAtMs: number;
}

export interface AppNotification {
  id: string;
  taskId: string | null;
  type: 'due_soon' | 'due_now' | 'completed' | 'overdue';
  title: string;
  content: string;
  isRead: boolean;
  createdAtMs: number;
}
```

```ts
// shared/contracts.ts
export type CloudSuccess<T> = { ok: true; data: T };
export type CloudFailure = {
  ok: false;
  code:
    | 'VALIDATION_ERROR'
    | 'NOT_FOUND'
    | 'FORBIDDEN'
    | 'CONFLICT'
    | 'SUBSCRIPTION_REQUIRED'
    | 'UPLOAD_REJECTED'
    | 'INTERNAL_ERROR';
  message: string;
};
export type CloudResult<T> = CloudSuccess<T> | CloudFailure;

export interface TaskListInput {
  scope: 'today' | 'upcoming' | 'all';
  keyword: string;
  selectedDateMs: number | null;
  cursor: string | null;
  limit: number;
}

export interface TaskListOutput {
  items: Task[];
  nextCursor: string | null;
}

export interface SaveTaskInput extends TaskInput {
  subscriptionAccepted: boolean;
}
```

```ts
// cloudfunctions/_shared/db.ts
// This adapter is created in Task 3. Production handlers call getDb(); tests inject Db directly.
export interface Db {
  users: {
    findOne(where: { openid: string }): Promise<{ openid: string; timezone: string } | null>;
    insert(doc: { openid: string; timezone: string; createdAtMs: number }): Promise<void>;
  };
  categories: {
    findOne(where: { _id?: string; ownerOpenid: string; name?: string }): Promise<(Category & { ownerOpenid: string }) | null>;
    findMany(where: { ownerOpenid: string }, sort: { sortOrder: 1 }): Promise<Category[]>;
    insert(doc: Omit<Category, 'id'> & { ownerOpenid: string }): Promise<void>;
    update(where: { _id: string; ownerOpenid: string }, patch: Partial<Category>): Promise<void>;
    delete(where: { _id: string; ownerOpenid: string }): Promise<void>;
  };
  tasks: {
    findOne(where: { _id: string; ownerOpenid: string }): Promise<(Task & { ownerOpenid: string }) | null>;
    findMany(where: { ownerOpenid: string }, options: { limit: number; cursor: string | null }): Promise<Array<Task & { ownerOpenid: string }>>;
    insert(doc: Task & { ownerOpenid: string }): Promise<void>;
    findDueReminders(range: { fromMs: number; toMs: number }): Promise<Array<Task & { ownerOpenid: string }>>;
    update(where: { _id: string; ownerOpenid?: string }, patch: Record<string, unknown>): Promise<void>;
    delete(where: { _id: string; ownerOpenid: string }): Promise<void>;
  };
  notifications: {
    findOne(where: { _id: string; ownerOpenid: string }): Promise<(AppNotification & { ownerOpenid: string }) | null>;
    findMany(where: { ownerOpenid: string }, options: { limit: number; cursor: string | null }): Promise<Array<AppNotification & { ownerOpenid: string }>>;
    insert(doc: Omit<AppNotification, 'id'> & { ownerOpenid: string }): Promise<void>;
    update(where: { _id: string; ownerOpenid: string }, patch: Partial<AppNotification>): Promise<void>;
    delete(where: { _id?: string; ownerOpenid: string }): Promise<void>;
  };
  reminderDeliveries: {
    insertIfAbsent(doc: { taskId: string; triggerAtMs: number | null }): Promise<boolean>;
    delete(where: { taskId: string }): Promise<void>;
  };
}

export function getDb(): Db {
  return wx.cloud.database() as unknown as Db;
}
```

### Task 1: Initialize the native Mini Program workspace and test harness

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vitest.config.ts`
- Create: `project.config.json`
- Create: `cloudbaserc.json`
- Create: `miniprogram/app.ts`
- Create: `miniprogram/app.json`
- Create: `miniprogram/app.wxss`
- Create: `tests/unit/project-config.test.ts`
- Create: `.gitignore`

**Interfaces:**
- Consumes: the global constraints in this plan.
- Produces: a TypeScript Mini Program project, Vitest command, CloudBase directory convention, and a Git repository used by every later task.

- [ ] **Step 1: Initialize Git and install the exact development dependencies.**

Run:

```powershell
git init
npm init -y
npm install mobx-miniprogram mobx-miniprogram-bindings zod dayjs
npm install -D typescript vitest miniprogram-api-typings miniprogram-automator @types/node
```

- [ ] **Step 2: Write the failing project-configuration test.**

```ts
// tests/unit/project-config.test.ts
import { describe, expect, it } from 'vitest';
import appConfig from '../../miniprogram/app.json';

describe('application configuration', () => {
  it('declares all MVP pages and uses a custom tab bar', () => {
    expect(appConfig.pages).toEqual([
      'pages/welcome/index',
      'pages/home/index',
      'pages/task-form/index',
      'pages/task-detail/index',
      'pages/calendar/index',
      'pages/notifications/index',
      'pages/profile/index',
      'pages/settings/categories/index',
    ]);
    expect(appConfig.tabBar.custom).toBe(true);
  });
});
```

- [ ] **Step 3: Run the test to verify the project has no configuration yet.**

Run: `npx vitest run tests/unit/project-config.test.ts`

Expected: FAIL because `miniprogram/app.json` does not exist.

- [ ] **Step 4: Create the minimal project configuration and app shell.**

```json
// miniprogram/app.json
{
  "pages": [
    "pages/welcome/index",
    "pages/home/index",
    "pages/task-form/index",
    "pages/task-detail/index",
    "pages/calendar/index",
    "pages/notifications/index",
    "pages/profile/index",
    "pages/settings/categories/index"
  ],
  "window": {
    "navigationBarTitleText": "Flowlist",
    "navigationBarTextStyle": "black",
    "navigationBarBackgroundColor": "#FFFFFF",
    "backgroundColor": "#F8FAFC"
  },
  "tabBar": { "custom": true }
}
```

```ts
// miniprogram/app.ts
App({
  globalData: { hasBootstrapped: false },
});
```

Configure `tsconfig.json` with `strict: true`, `noUncheckedIndexedAccess: true`, and `types: ["miniprogram-api-typings"]`. Configure the `test` script as `vitest run` and the `test:watch` script as `vitest`.

- [ ] **Step 5: Run the configuration test and type-check.**

Run:

```powershell
npx vitest run tests/unit/project-config.test.ts
npx tsc --noEmit
```

Expected: both commands PASS.

- [ ] **Step 6: Commit the project baseline.**

```powershell
git add package.json package-lock.json tsconfig.json vitest.config.ts project.config.json cloudbaserc.json miniprogram tests .gitignore
git commit -m "chore: initialize Flowlist Mini Program workspace"
```

### Task 2: Define shared task contracts, validation, and date calculations

**Files:**
- Create: `shared/domain.ts`
- Create: `shared/contracts.ts`
- Create: `shared/schemas.ts`
- Create: `shared/reminder.ts`
- Create: `tests/unit/schemas.test.ts`
- Create: `tests/unit/reminder.test.ts`

**Interfaces:**
- Consumes: Task 1 TypeScript and Vitest setup.
- Produces: `TaskInput`, `Task`, `Reminder`, `TaskListInput`, `CloudResult<T>`, `taskInputSchema`, and `calculateReminderTriggerAtMs()` for pages and cloud functions.

- [ ] **Step 1: Write failing validation and reminder tests.**

```ts
// tests/unit/schemas.test.ts
import { describe, expect, it } from 'vitest';
import { taskInputSchema } from '../../shared/schemas';

describe('taskInputSchema', () => {
  it('rejects an empty title', () => {
    const result = taskInputSchema.safeParse({ title: '', note: '', priority: 'medium', categoryId: null, dueAtMs: null, timezone: 'Asia/Shanghai', reminder: { enabled: false, offset: 'at_due', triggerAtMs: null, status: 'off', templateId: null, subscriptionGrantedAtMs: null }, subtasks: [], attachments: [] });
    expect(result.success).toBe(false);
  });
});
```

```ts
// tests/unit/reminder.test.ts
import { describe, expect, it } from 'vitest';
import { calculateReminderTriggerAtMs } from '../../shared/reminder';

describe('calculateReminderTriggerAtMs', () => {
  it('subtracts thirty minutes from a due timestamp', () => {
    expect(calculateReminderTriggerAtMs(1_800_000, '30m')).toBe(0);
  });
});
```

- [ ] **Step 2: Run the tests to verify the contracts are absent.**

Run: `npx vitest run tests/unit/schemas.test.ts tests/unit/reminder.test.ts`

Expected: FAIL because the shared modules do not exist.

- [ ] **Step 3: Implement the shared types and minimal rules.**

Create the exact `shared/domain.ts` and `shared/contracts.ts` interfaces shown in **Shared Interfaces**. Implement the following schema and reminder function:

```ts
// shared/schemas.ts
import { z } from 'zod';

export const taskInputSchema = z.object({
  id: z.string().min(1).optional(),
  title: z.string().trim().min(1).max(120),
  note: z.string().max(4_000),
  categoryId: z.string().min(1).nullable(),
  priority: z.enum(['low', 'medium', 'high']),
  dueAtMs: z.number().int().positive().nullable(),
  timezone: z.string().min(1).max(64),
  reminder: z.object({
    enabled: z.boolean(),
    offset: z.enum(['at_due', '10m', '30m', '1h', '1d']),
    triggerAtMs: z.number().int().positive().nullable(),
    status: z.enum(['off', 'pending', 'skipped', 'sent', 'failed']),
    templateId: z.string().min(1).nullable(),
    subscriptionGrantedAtMs: z.number().int().positive().nullable(),
  }),
  subtasks: z.array(z.object({ id: z.string().min(1), title: z.string().trim().min(1).max(120), completed: z.boolean(), sortOrder: z.number().int().min(0) })).max(50),
  attachments: z.array(z.object({ fileId: z.string().min(1), name: z.string().min(1).max(255), mimeType: z.enum(['image/jpeg', 'image/png', 'application/pdf']), sizeBytes: z.number().int().positive().max(10 * 1024 * 1024) })).max(5),
});
```

```ts
// shared/reminder.ts
import type { ReminderOffset } from './domain';

const offsetMs: Record<ReminderOffset, number> = {
  at_due: 0,
  '10m': 10 * 60 * 1_000,
  '30m': 30 * 60 * 1_000,
  '1h': 60 * 60 * 1_000,
  '1d': 24 * 60 * 60 * 1_000,
};

export function calculateReminderTriggerAtMs(dueAtMs: number, offset: ReminderOffset): number {
  return dueAtMs - offsetMs[offset];
}
```

- [ ] **Step 4: Extend the tests for attachment limits and the one-day offset, then run them.**

```ts
const sixAttachments = Array.from({ length: 6 }, (_, index) => ({ fileId: `f_${index}`, name: `f_${index}.pdf`, mimeType: 'application/pdf' as const, sizeBytes: 1 }));
const tooManyAttachments = {
  title: '归档资料', note: '', categoryId: null, priority: 'medium' as const, dueAtMs: null,
  timezone: 'Asia/Shanghai', reminder: { enabled: false, offset: 'at_due' as const, triggerAtMs: null, status: 'off' as const, templateId: null, subscriptionGrantedAtMs: null },
  subtasks: [], attachments: sixAttachments,
};
expect(calculateReminderTriggerAtMs(86_400_000, '1d')).toBe(0);
expect(taskInputSchema.safeParse(tooManyAttachments).success).toBe(false);
```

Run: `npx vitest run tests/unit/schemas.test.ts tests/unit/reminder.test.ts`

Expected: PASS.

- [ ] **Step 5: Commit the contract boundary.**

```powershell
git add shared tests/unit
git commit -m "feat: define Flowlist task domain contracts"
```

### Task 3: Implement CloudBase user bootstrap and category management

**Files:**
- Create: `cloudfunctions/bootstrap-user/index.ts`
- Create: `cloudfunctions/bootstrap-user/package.json`
- Create: `cloudfunctions/categories/index.ts`
- Create: `cloudfunctions/categories/package.json`
- Create: `cloudfunctions/_shared/db.ts`
- Create: `miniprogram/services/cloud.ts`
- Create: `miniprogram/services/categories.ts`
- Create: `miniprogram/stores/session.ts`
- Create: `tests/cloudfunctions/bootstrap-user.test.ts`
- Create: `tests/cloudfunctions/categories.test.ts`

**Interfaces:**
- Consumes: `Category` and `CloudResult<T>` from Task 2.
- Produces: `bootstrapUser(): Promise<{ categories: Category[]; timezone: string }>` and `saveCategory(input: { id?: string; name: string; color: string }): Promise<Category>` for Task 7 and Task 10.

- [ ] **Step 1: Write a failing bootstrap test using a mocked CloudBase context.**

```ts
import { describe, expect, it, vi } from 'vitest';
import { bootstrapUserHandler } from '../../cloudfunctions/bootstrap-user/index';
import type { Db } from '../../cloudfunctions/_shared/db';

function createFakeDb(): Db {
  const users: Array<{ openid: string; timezone: string }> = [];
  const categories: Array<Category & { ownerOpenid: string }> = [];
  return {
    users: {
      findOne: async ({ openid }) => users.find((user) => user.openid === openid) ?? null,
      insert: async (user) => { users.push(user); },
    },
    categories: {
      findOne: async ({ ownerOpenid, name }) => categories.find((item) => item.ownerOpenid === ownerOpenid && item.name === name) ?? null,
      findMany: async ({ ownerOpenid }) => categories.filter((item) => item.ownerOpenid === ownerOpenid).sort((a, b) => a.sortOrder - b.sortOrder),
      insert: async (category) => { categories.push({ ...category, id: `c_${categories.length + 1}` }); },
    },
    tasks: {} as Db['tasks'],
    notifications: {} as Db['notifications'],
    reminderDeliveries: {} as Db['reminderDeliveries'],
  };
}

it('creates Work and Personal only for a first-time OpenID', async () => {
  const db = createFakeDb();
  const result = await bootstrapUserHandler({}, { openid: 'o_user_1', db, nowMs: 100 });
  expect(result.ok).toBe(true);
  if (result.ok) expect(result.data.categories.map((item) => item.name)).toEqual(['Work', 'Personal']);
});
```

- [ ] **Step 2: Run the cloud-function tests to verify the handler does not exist.**

Run: `npx vitest run tests/cloudfunctions/bootstrap-user.test.ts tests/cloudfunctions/categories.test.ts`

Expected: FAIL because the cloud-function handlers do not exist.

- [ ] **Step 3: Implement ownership-derived user and category handlers.**

```ts
// cloudfunctions/bootstrap-user/index.ts
export async function bootstrapUserHandler(
  _event: Record<string, never>,
  deps: { openid: string; db: Db; nowMs: number },
): Promise<CloudResult<{ categories: Category[]; timezone: string }>> {
  const user = await deps.db.users.findOne({ openid: deps.openid });
  if (!user) {
    await deps.db.users.insert({ openid: deps.openid, timezone: 'Asia/Shanghai', createdAtMs: deps.nowMs });
    await deps.db.categories.insert({ ownerOpenid: deps.openid, name: 'Work', color: '#3B82F6', isSystem: true, sortOrder: 0 });
    await deps.db.categories.insert({ ownerOpenid: deps.openid, name: 'Personal', color: '#10B981', isSystem: true, sortOrder: 1 });
  }
  const categories = await deps.db.categories.findMany({ ownerOpenid: deps.openid }, { sortOrder: 1 });
  return { ok: true, data: { categories, timezone: user?.timezone ?? 'Asia/Shanghai' } };
}
```

Create `cloudfunctions/_shared/db.ts` using the exact `Db` and `getDb()` adapter shown in **Shared Interfaces**, and import `Db` from that file in every cloud-function handler.

Implement `categoriesHandler(event, deps)` with actions `list`, `save`, and `delete`. Reject blank or duplicate names with `VALIDATION_ERROR`; reject deleting an `isSystem` category or a category referenced by a task with `CONFLICT`.

```ts
export async function categoriesHandler(
  event: { action: 'list' | 'save' | 'delete'; input: { id?: string; name?: string; color?: string } },
  deps: { openid: string; db: Db },
): Promise<CloudResult<Category[] | Category | void>> {
  if (event.action === 'list') return { ok: true, data: await deps.db.categories.findMany({ ownerOpenid: deps.openid }, { sortOrder: 1 }) };
  if (event.action === 'save') return saveOwnedCategory(event.input, deps);
  return deleteOwnedCategory(event.input.id ?? '', deps);
}
```

- [ ] **Step 4: Implement the Mini Program cloud client and category service.**

```ts
// miniprogram/services/cloud.ts
export async function callCloud<T>(name: string, data: unknown): Promise<T> {
  const result = await wx.cloud.callFunction({ name, data });
  const payload = result.result as CloudResult<T>;
  if (!payload.ok) throw new Error(`${payload.code}:${payload.message}`);
  return payload.data;
}
```

```ts
// miniprogram/services/categories.ts
export const bootstrapUser = () => callCloud<{ categories: Category[]; timezone: string }>('bootstrap-user', {});
export const saveCategory = (input: { id?: string; name: string; color: string }) => callCloud<Category>('categories', { action: 'save', input });
```

- [ ] **Step 5: Run tests and type-check.**

Run:

```powershell
npx vitest run tests/cloudfunctions/bootstrap-user.test.ts tests/cloudfunctions/categories.test.ts
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 6: Commit the identity and category baseline.**

```powershell
git add cloudfunctions miniprogram/services miniprogram/stores tests/cloudfunctions
git commit -m "feat: add private user bootstrap and categories"
```

### Task 4: Implement task list and create-task cloud contracts

**Files:**
- Create: `cloudfunctions/tasks/index.ts`
- Create: `cloudfunctions/tasks/package.json`
- Create: `miniprogram/services/tasks.ts`
- Create: `tests/cloudfunctions/tasks-list.test.ts`
- Create: `tests/cloudfunctions/tasks-save.test.ts`

**Interfaces:**
- Consumes: `TaskInput`, `Task`, `TaskListInput`, `TaskListOutput`, `taskInputSchema`, `calculateReminderTriggerAtMs`, and `callCloud<T>`.
- Produces: `listTasks(input: TaskListInput): Promise<TaskListOutput>` and `saveTask(input: SaveTaskInput): Promise<Task>` for Task 7 and Task 8.

- [ ] **Step 1: Write failing task-list tests for ownership and today filtering.**

```ts
const validReminder = (overrides: Partial<Reminder> = {}): Reminder => ({
  enabled: false,
  offset: 'at_due',
  triggerAtMs: null,
  status: 'off',
  templateId: null,
  subscriptionGrantedAtMs: null,
  ...overrides,
});

const validSaveInput = (overrides: Partial<SaveTaskInput> = {}): SaveTaskInput => ({
  title: '整理客户方案', note: '', categoryId: null, priority: 'medium', dueAtMs: null,
  timezone: 'Asia/Shanghai', reminder: validReminder(), subtasks: [], attachments: [], subscriptionAccepted: false,
  ...overrides,
});

const createTasksDb = (tasks: Array<Task & { ownerOpenid: string }>) => ({ tasks }) as unknown as Db;

const deps = (overrides: Partial<{ openid: string; db: Db; nowMs: number; timezone: string }> = {}) => ({
  openid: 'o_current', db: createTasksDb([]), nowMs: 1_000, timezone: 'Asia/Shanghai', ...overrides,
});

it('returns only the current users tasks in the today scope', async () => {
  const db = createTasksDb([
    { _id: 'a', ownerOpenid: 'o_current', title: 'Today', dueAtMs: 1_000, status: 'todo' },
    { _id: 'b', ownerOpenid: 'o_other', title: 'Other user', dueAtMs: 1_000, status: 'todo' },
  ]);
  const result = await tasksHandler({ action: 'list', input: { scope: 'today', keyword: '', selectedDateMs: 0, cursor: null, limit: 20 } }, { openid: 'o_current', db, nowMs: 1_000, timezone: 'Asia/Shanghai' });
  expect(result).toMatchObject({ ok: true, data: { items: [{ id: 'a', title: 'Today' }] } });
});
```

- [ ] **Step 2: Write the failing save-task test for reminder trigger calculation.**

```ts
it('stores a pending reminder when the due time and accepted subscription are present', async () => {
  const result = await tasksHandler({ action: 'save', input: validSaveInput({ dueAtMs: 3_600_000, reminder: validReminder({ enabled: true, offset: '30m' }), subscriptionAccepted: true }) }, deps());
  expect(result).toMatchObject({ ok: true, data: { reminder: { triggerAtMs: 1_800_000, status: 'pending' } } });
});
```

- [ ] **Step 3: Run tests to verify the task handler is absent.**

Run: `npx vitest run tests/cloudfunctions/tasks-list.test.ts tests/cloudfunctions/tasks-save.test.ts`

Expected: FAIL because `tasksHandler` does not exist.

- [ ] **Step 4: Implement `list` and `save` actions in `tasksHandler`.**

```ts
export async function tasksHandler(
  event: { action: 'list' | 'save'; input: TaskListInput | SaveTaskInput },
  deps: { openid: string; db: Db; nowMs: number; timezone: string },
): Promise<CloudResult<TaskListOutput | Task>> {
  if (event.action === 'list') return listOwnedTasks(event.input as TaskListInput, deps);
  return saveOwnedTask(event.input as SaveTaskInput, deps);
}
```

`listOwnedTasks()` must start every query with `{ ownerOpenid: deps.openid }`, trim the keyword, cap `limit` at 50, and return tasks sorted by incomplete-first then `dueAtMs` ascending. `saveOwnedTask()` must parse `TaskInput` using `taskInputSchema`, verify category ownership when `categoryId` is non-null, calculate `triggerAtMs` only when `reminder.enabled` and `dueAtMs` are present, and set reminder status to `pending` only when `subscriptionAccepted` is true. Otherwise set `skipped`.

- [ ] **Step 5: Add the Mini Program service functions and run tests.**

```ts
// miniprogram/services/tasks.ts
export const listTasks = (input: TaskListInput) => callCloud<TaskListOutput>('tasks', { action: 'list', input });
export const saveTask = (input: SaveTaskInput) => callCloud<Task>('tasks', { action: 'save', input });
```

Run:

```powershell
npx vitest run tests/cloudfunctions/tasks-list.test.ts tests/cloudfunctions/tasks-save.test.ts
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 6: Commit task creation and listing.**

```powershell
git add cloudfunctions/tasks miniprogram/services/tasks.ts tests/cloudfunctions
git commit -m "feat: add private task creation and listing"
```

### Task 5: Add task update, completion, deletion, subtasks, and attachment registration

**Files:**
- Modify: `cloudfunctions/tasks/index.ts`
- Create: `cloudfunctions/task-files/index.ts`
- Create: `cloudfunctions/task-files/package.json`
- Modify: `miniprogram/services/tasks.ts`
- Create: `miniprogram/services/upload.ts`
- Create: `tests/cloudfunctions/tasks-mutation.test.ts`
- Create: `tests/cloudfunctions/task-files.test.ts`

**Interfaces:**
- Consumes: `tasksHandler`, `Task`, `TaskInput`, `TaskAttachment`, and `taskInputSchema`.
- Produces: `toggleTask(id: string, completed: boolean): Promise<Task>`, `deleteTask(id: string): Promise<void>`, and `registerAttachment(input: { taskId: string; attachment: TaskAttachment }): Promise<TaskAttachment>`.

- [ ] **Step 1: Write failing mutation tests.**

```ts
it('cannot toggle a task owned by another user', async () => {
  const result = await tasksHandler({ action: 'toggle', input: { id: 'other-task', completed: true } }, deps({ openid: 'o_current' }));
  expect(result).toEqual({ ok: false, code: 'NOT_FOUND', message: '任务不存在' });
});

it('marks completion time when completing a task', async () => {
  const result = await tasksHandler({ action: 'toggle', input: { id: 'owned-task', completed: true } }, deps({ nowMs: 500 }));
  expect(result).toMatchObject({ ok: true, data: { status: 'completed', completedAtMs: 500 } });
});
```

- [ ] **Step 2: Run the mutation tests to verify the actions are absent.**

Run: `npx vitest run tests/cloudfunctions/tasks-mutation.test.ts tests/cloudfunctions/task-files.test.ts`

Expected: FAIL because the `toggle`, `delete`, and file handlers are absent.

- [ ] **Step 3: Implement the mutation actions and attachment guard.**

Add `toggle`, `delete`, and `update` action variants to `tasksHandler`. Every mutation must locate the task by `{ _id: id, ownerOpenid: deps.openid }`. `toggle` sets `{ status: completed ? 'completed' : 'todo', completedAtMs: completed ? deps.nowMs : null }`. `delete` deletes the task, its `notifications`, its `reminderDeliveries`, and calls the file cleanup handler with its attachment file IDs.

Replace the Task 4 handler signature with this expanded, type-consistent signature:

```ts
export type TasksAction = 'list' | 'save' | 'update' | 'toggle' | 'delete' | 'calendar';
export type TaskMutationInput = { id: string; completed?: boolean; patch?: TaskInput };

export async function tasksHandler(
  event: { action: TasksAction; input: TaskListInput | SaveTaskInput | TaskMutationInput | { monthStartMs: number; monthEndMs: number } },
  deps: { openid: string; db: Db; nowMs: number; timezone: string },
): Promise<CloudResult<TaskListOutput | Task | Task[] | void>> {
  if (event.action === 'list') return listOwnedTasks(event.input as TaskListInput, deps);
  if (event.action === 'save') return saveOwnedTask(event.input as SaveTaskInput, deps);
  if (event.action === 'update') return updateOwnedTask(event.input as TaskMutationInput, deps);
  if (event.action === 'toggle') return toggleOwnedTask(event.input as TaskMutationInput, deps);
  if (event.action === 'delete') return deleteOwnedTask(event.input as TaskMutationInput, deps);
  return listCalendarTasks(event.input as { monthStartMs: number; monthEndMs: number }, deps);
}
```

```ts
// cloudfunctions/task-files/index.ts
const allowedMimeTypes = new Set(['image/jpeg', 'image/png', 'application/pdf']);

export function validateAttachment(attachment: TaskAttachment): CloudResult<TaskAttachment> {
  if (!allowedMimeTypes.has(attachment.mimeType) || attachment.sizeBytes > 10 * 1024 * 1024) {
    return { ok: false, code: 'UPLOAD_REJECTED', message: '仅支持 10MB 以内的图片或 PDF' };
  }
  return { ok: true, data: attachment };
}
```

- [ ] **Step 4: Implement client upload sequencing.**

```ts
// miniprogram/services/upload.ts
export async function uploadAttachment(taskId: string, filePath: string, name: string, mimeType: TaskAttachment['mimeType']): Promise<TaskAttachment> {
  const info = await wx.getFileInfo({ filePath });
  const upload = await wx.cloud.uploadFile({ cloudPath: `tasks/${taskId}/${Date.now()}-${name}`, filePath });
  return callCloud<TaskAttachment>('task-files', {
    action: 'register',
    input: { taskId, attachment: { fileId: upload.fileID, name, mimeType, sizeBytes: info.size } },
  });
}
```

- [ ] **Step 5: Run the mutation and upload tests.**

Run: `npx vitest run tests/cloudfunctions/tasks-mutation.test.ts tests/cloudfunctions/task-files.test.ts`

Expected: PASS.

- [ ] **Step 6: Commit task mutations and attachment protection.**

```powershell
git add cloudfunctions miniprogram/services tests/cloudfunctions
git commit -m "feat: add task mutations and attachment validation"
```

### Task 6: Implement notifications, notification read state, and calendar query contracts

**Files:**
- Create: `cloudfunctions/notifications/index.ts`
- Create: `cloudfunctions/notifications/package.json`
- Modify: `cloudfunctions/tasks/index.ts`
- Create: `miniprogram/services/notifications.ts`
- Create: `tests/cloudfunctions/notifications.test.ts`
- Create: `tests/cloudfunctions/calendar.test.ts`

**Interfaces:**
- Consumes: `AppNotification`, `TaskListOutput`, `callCloud<T>`, and `tasksHandler`.
- Produces: `listNotifications(cursor: string | null): Promise<{ items: AppNotification[]; nextCursor: string | null }>`, `markNotificationRead(id: string): Promise<void>`, `clearNotifications(): Promise<void>`, and `listCalendarTasks(monthStartMs: number, monthEndMs: number): Promise<Task[]>`.

- [ ] **Step 1: Write failing notification and calendar tests.**

```ts
it('marks only the owners notification as read', async () => {
  const result = await notificationsHandler({ action: 'read', input: { id: 'n-other' } }, deps({ openid: 'o_current' }));
  expect(result).toEqual({ ok: false, code: 'NOT_FOUND', message: '通知不存在' });
});

it('returns dated tasks inside a closed month range', async () => {
  const result = await tasksHandler({ action: 'calendar', input: { monthStartMs: 1_000, monthEndMs: 2_000 } }, deps());
  expect(result).toMatchObject({ ok: true, data: [{ id: 'in-month' }] });
});
```

- [ ] **Step 2: Run tests to verify the handlers are absent.**

Run: `npx vitest run tests/cloudfunctions/notifications.test.ts tests/cloudfunctions/calendar.test.ts`

Expected: FAIL because the notification and calendar actions are absent.

- [ ] **Step 3: Implement ownership-scoped notification actions.**

`notificationsHandler` must support `list`, `read`, and `clear`. `list` queries only `{ ownerOpenid: deps.openid }` ordered by `createdAtMs` descending. `read` updates one document matching both `_id` and `ownerOpenid`. `clear` deletes documents matching the same owner condition and no other documents.

```ts
export async function notificationsHandler(
  event: { action: 'list' | 'read' | 'clear'; input: { id?: string; cursor?: string | null } },
  deps: { openid: string; db: Db },
): Promise<CloudResult<{ items: AppNotification[]; nextCursor: string | null } | void>> {
  if (event.action === 'list') return listOwnedNotifications(event.input.cursor ?? null, deps);
  if (event.action === 'read') return markOwnedNotificationRead(event.input.id ?? '', deps);
  return clearOwnedNotifications(deps);
}
```

Extend `tasksHandler` with the `calendar` action. It must return tasks where `ownerOpenid` matches, `dueAtMs` is not null, and `monthStartMs <= dueAtMs <= monthEndMs`.

The `calendar` branch is the final branch in the expanded `tasksHandler()` signature introduced in Task 5; do not create a second handler or a second task-query API.

- [ ] **Step 4: Implement Mini Program notification service functions.**

```ts
// miniprogram/services/notifications.ts
export const listNotifications = (cursor: string | null) =>
  callCloud<{ items: AppNotification[]; nextCursor: string | null }>('notifications', { action: 'list', input: { cursor } });
export const markNotificationRead = (id: string) => callCloud<void>('notifications', { action: 'read', input: { id } });
export const clearNotifications = () => callCloud<void>('notifications', { action: 'clear', input: {} });
```

- [ ] **Step 5: Run tests and type-check.**

Run:

```powershell
npx vitest run tests/cloudfunctions/notifications.test.ts tests/cloudfunctions/calendar.test.ts
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 6: Commit calendar and in-app notification contracts.**

```powershell
git add cloudfunctions miniprogram/services tests/cloudfunctions
git commit -m "feat: add calendar and in-app notifications"
```

### Task 7: Build the welcome, app shell, task-list, and task-editor UI

**Files:**
- Create: `miniprogram/pages/welcome/index.ts`
- Create: `miniprogram/pages/welcome/index.wxml`
- Create: `miniprogram/pages/welcome/index.wxss`
- Create: `miniprogram/pages/home/index.ts`
- Create: `miniprogram/pages/home/index.wxml`
- Create: `miniprogram/pages/home/index.wxss`
- Create: `miniprogram/pages/task-form/index.ts`
- Create: `miniprogram/pages/task-form/index.wxml`
- Create: `miniprogram/pages/task-form/index.wxss`
- Create: `miniprogram/components/task-card/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/components/task-editor/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/components/bottom-tab-bar/index.{ts,wxml,wxss,json}`
- Create: `tests/unit/task-editor.test.ts`
- Create: `tests/e2e/task-create.spec.ts`

**Interfaces:**
- Consumes: `bootstrapUser`, `listTasks`, `saveTask`, `toggleTask`, `Task`, `TaskInput`, and `TaskListInput`.
- Produces: a user can enter by WeChat identity, create a task, see it in the list, search it, and toggle completion.

- [ ] **Step 1: Write a failing task-editor behavior test.**

```ts
import { describe, expect, it } from 'vitest';
import { buildTaskDraft } from '../../miniprogram/components/task-editor/index';

describe('buildTaskDraft', () => {
  it('returns a Chinese validation error for an empty title', () => {
    expect(buildTaskDraft({ title: '   ' }).error).toBe('请输入任务标题');
  });
});
```

- [ ] **Step 2: Run the unit test to verify the editor helper does not exist.**

Run: `npx vitest run tests/unit/task-editor.test.ts`

Expected: FAIL because `buildTaskDraft` does not exist.

- [ ] **Step 3: Implement the minimal editor helper and UI bindings.**

```ts
// miniprogram/components/task-editor/index.ts
export function buildTaskDraft(input: Partial<TaskInput>): { value?: TaskInput; error?: string } {
  const title = (input.title ?? '').trim();
  if (!title) return { error: '请输入任务标题' };
  return {
    value: {
      title,
      note: input.note ?? '',
      categoryId: input.categoryId ?? null,
      priority: input.priority ?? 'medium',
      dueAtMs: input.dueAtMs ?? null,
      timezone: input.timezone ?? 'Asia/Shanghai',
      reminder: input.reminder ?? { enabled: false, offset: 'at_due', triggerAtMs: null, status: 'off', templateId: null, subscriptionGrantedAtMs: null },
      subtasks: input.subtasks ?? [],
      attachments: input.attachments ?? [],
    },
  };
}
```

Welcome must call `bootstrapUser()` and then `wx.reLaunch({ url: '/pages/home/index' })`. Home must maintain `scope`, `keyword`, and `items`, call `listTasks({ scope, keyword, selectedDateMs: null, cursor: null, limit: 20 })`, and debounce keyword input by 300 ms. The task form must call `buildTaskDraft()`, show its exact error via `wx.showToast`, and call `saveTask({ ...draft, subscriptionAccepted: false })` when the reminder is disabled.

- [ ] **Step 4: Add an end-to-end test for the core task path.**

```ts
// tests/e2e/task-create.spec.ts
import automator from 'miniprogram-automator';

it('creates and completes a task', async () => {
  const miniProgram = await automator.launch({ projectPath: process.cwd() });
  const page = await miniProgram.reLaunch('/pages/task-form/index');
  await page.$('input[data-testid="task-title"]').then((node) => node?.input('整理客户方案'));
  await page.$('button[data-testid="save-task"]').then((node) => node?.tap());
  await miniProgram.navigateTo('/pages/home/index');
  expect(await page.data('items')).toContainEqual(expect.objectContaining({ title: '整理客户方案' }));
  await miniProgram.close();
});
```

- [ ] **Step 5: Run unit test, compile in Developer Tools, and run the e2e test.**

Run:

```powershell
npx vitest run tests/unit/task-editor.test.ts
npm run devtools:compile
npx vitest run tests/e2e/task-create.spec.ts
```

Expected: all commands PASS; manual check confirms the home card follows the provided wireframe.

- [ ] **Step 6: Commit the core user interface.**

```powershell
git add miniprogram/pages miniprogram/components tests
git commit -m "feat: add Flowlist task list and editor UI"
```

### Task 8: Build task details, calendar, attachments, and category settings UI

**Files:**
- Create: `miniprogram/pages/task-detail/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/pages/calendar/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/pages/settings/categories/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/components/month-calendar/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/components/empty-state/index.{ts,wxml,wxss,json}`
- Create: `tests/unit/month-calendar.test.ts`
- Create: `tests/e2e/task-detail-calendar.spec.ts`

**Interfaces:**
- Consumes: Task 3 category services; Tasks 4 through 6 task, calendar, attachment, and notification services.
- Produces: editable task detail, monthly date selection, category management, and image/PDF attachment controls.

- [ ] **Step 1: Write a failing calendar-marker test.**

```ts
import { describe, expect, it } from 'vitest';
import { buildTaskDateSet } from '../../miniprogram/components/month-calendar/index';

it('marks each date that has at least one due task', () => {
  expect(buildTaskDateSet([{ dueAtMs: Date.UTC(2026, 6, 12) }, { dueAtMs: Date.UTC(2026, 6, 12) }], 'Asia/Shanghai')).toEqual(new Set(['2026-07-12']));
});
```

- [ ] **Step 2: Run tests to verify the calendar helper is absent.**

Run: `npx vitest run tests/unit/month-calendar.test.ts tests/e2e/task-detail-calendar.spec.ts`

Expected: FAIL because `buildTaskDateSet` and the pages do not exist.

- [ ] **Step 3: Implement calendar, detail, and attachment interactions.**

```ts
// miniprogram/components/month-calendar/index.ts
export function buildTaskDateSet(tasks: Array<{ dueAtMs: number | null }>, timezone: string): Set<string> {
  return new Set(tasks.filter((task) => task.dueAtMs !== null).map((task) => formatDateKey(task.dueAtMs as number, timezone)));
}
```

Task detail must load its `id` from `options.id`, use the existing `saveTask`, `toggleTask`, and `deleteTask` functions, and require `wx.showModal({ title: '删除任务', content: '删除后无法恢复，确定删除吗？' })` confirmation before deletion. Category settings must call `saveCategory()` and surface a `CONFLICT` response as `该分类仍有关联任务，暂时无法删除`.

For attachment selection, call `wx.chooseMedia()` for images and `wx.chooseMessageFile({ type: 'file', extension: ['pdf'] })` for PDFs. Pass the selected path through `uploadAttachment()` before adding it to the draft.

- [ ] **Step 4: Add an end-to-end test for date selection and deletion confirmation.**

```ts
it('shows a due task after selecting its calendar date and requires confirmation before deletion', async () => {
  const miniProgram = await automator.launch({ projectPath: process.cwd() });
  const calendar = await miniProgram.reLaunch('/pages/calendar/index');
  await calendar.$('[data-testid="date-2026-07-12"]').then((node) => node?.tap());
  expect(await calendar.data('selectedTasks')).toContainEqual(expect.objectContaining({ title: '整理客户方案' }));
  await miniProgram.close();
});
```

- [ ] **Step 5: Run focused tests and manually inspect attachment errors.**

Run:

```powershell
npx vitest run tests/unit/month-calendar.test.ts tests/e2e/task-detail-calendar.spec.ts
npx tsc --noEmit
```

Expected: PASS. On a real device, an 11 MB file and a non-image/non-PDF file show `仅支持 10MB 以内的图片或 PDF`.

- [ ] **Step 6: Commit task detail and planning views.**

```powershell
git add miniprogram/pages miniprogram/components tests
git commit -m "feat: add task detail calendar and attachments"
```

### Task 9: Implement opt-in subscription reminders and delivery idempotency

**Files:**
- Create: `cloudfunctions/send-due-reminders/index.ts`
- Create: `cloudfunctions/send-due-reminders/package.json`
- Create: `cloudfunctions/send-due-reminders/config.json`
- Create: `miniprogram/services/reminders.ts`
- Create: `miniprogram/utils/subscription.ts`
- Modify: `miniprogram/pages/task-form/index.ts`
- Modify: `miniprogram/pages/task-detail/index.ts`
- Create: `tests/cloudfunctions/send-due-reminders.test.ts`
- Create: `tests/unit/subscription.test.ts`

**Interfaces:**
- Consumes: `Reminder`, `Task`, `AppNotification`, `saveTask`, and the approved WeChat subscription-message template ID stored in CloudBase function environment variable `FLOWLIST_REMINDER_TEMPLATE_ID`.
- Produces: `requestReminderSubscription(templateId: string): Promise<boolean>` and a scheduled `sendDueRemindersHandler(event, deps)` that sends each due reminder once.

- [ ] **Step 1: Confirm the platform gate before writing reminder code.**

In WeChat Public Platform, record the approved task-reminder template ID, attach it to the production Mini Program environment, and set the cloud-function environment variable `FLOWLIST_REMINDER_TEMPLATE_ID` to that exact value. Create a development template entry in the development environment. If no eligible template is available, stop this task, set the feature flag `subscriptionRemindersEnabled` to `false`, and remove every external-reminder claim from the release copy.

- [ ] **Step 2: Write failing unit and cloud-function tests.**

```ts
// tests/unit/subscription.test.ts
import { describe, expect, it, vi } from 'vitest';
import { requestReminderSubscription } from '../../miniprogram/utils/subscription';

it('returns true only when the approved template is accepted', async () => {
  vi.stubGlobal('wx', { requestSubscribeMessage: vi.fn().mockResolvedValue({ tmpl_1: 'accept' }) });
  await expect(requestReminderSubscription('tmpl_1')).resolves.toBe(true);
});
```

```ts
// tests/cloudfunctions/send-due-reminders.test.ts
it('claims and sends one pending reminder only once', async () => {
  const result = await sendDueRemindersHandler({}, deps({ nowMs: 10_000 }));
  expect(result).toMatchObject({ sentCount: 1, skippedCount: 0 });
  const second = await sendDueRemindersHandler({}, deps({ nowMs: 10_000 }));
  expect(second).toMatchObject({ sentCount: 0, skippedCount: 1 });
});
```

- [ ] **Step 3: Run tests to verify no subscription or scheduled handler exists.**

Run: `npx vitest run tests/unit/subscription.test.ts tests/cloudfunctions/send-due-reminders.test.ts`

Expected: FAIL because the modules do not exist.

- [ ] **Step 4: Implement client subscription handling.**

```ts
// miniprogram/utils/subscription.ts
export async function requestReminderSubscription(templateId: string): Promise<boolean> {
  try {
    const result = await wx.requestSubscribeMessage({ tmplIds: [templateId] });
    return result[templateId] === 'accept';
  } catch {
    return false;
  }
}
```

When a task has `reminder.enabled === true`, task-form and task-detail must call this function immediately after the user taps save. They must then call `saveTask()` with `subscriptionAccepted` set to the returned boolean. If false, display `任务已保存，但未开启微信提醒` and retain the task with reminder status `skipped`.

- [ ] **Step 5: Implement the scheduled cloud function with atomic claim.**

```ts
export async function sendDueRemindersHandler(
  _event: Record<string, never>,
  deps: { db: Db; nowMs: number; templateId: string; sendSubscribeMessage: (openid: string, task: Task) => Promise<void> },
): Promise<{ sentCount: number; skippedCount: number }> {
  const candidates = await deps.db.tasks.findDueReminders({ fromMs: deps.nowMs - 5 * 60 * 1_000, toMs: deps.nowMs });
  let sentCount = 0;
  let skippedCount = 0;
  for (const task of candidates) {
    const claimed = await deps.db.reminderDeliveries.insertIfAbsent({ taskId: task.id, triggerAtMs: task.reminder.triggerAtMs });
    if (!claimed) { skippedCount += 1; continue; }
    await deps.db.notifications.insert({ ownerOpenid: task.ownerOpenid, taskId: task.id, type: 'due_soon', title: '任务提醒', content: `「${task.title}」即将到期`, isRead: false, createdAtMs: deps.nowMs });
    await deps.sendSubscribeMessage(task.ownerOpenid, task);
    await deps.db.tasks.update({ _id: task.id }, { 'reminder.status': 'sent' });
    sentCount += 1;
  }
  return { sentCount, skippedCount };
}
```

Configure `config.json` with the five-minute schedule expression supported by the deployed CloudBase environment. The function must record an error and set reminder status `failed` when message delivery rejects, without retrying a permanently rejected subscription.

- [ ] **Step 6: Run tests and conduct real-device validation.**

Run: `npx vitest run tests/unit/subscription.test.ts tests/cloudfunctions/send-due-reminders.test.ts`

Expected: PASS.

On Android and iOS WeChat real devices, validate all four cases: accept then receive one message, reject then save task, tap message then open task detail, and run the scheduler twice without a duplicate message.

- [ ] **Step 7: Commit the reminder feature.**

```powershell
git add cloudfunctions/send-due-reminders miniprogram tests
git commit -m "feat: add opt-in task reminder delivery"
```

### Task 10: Build notification, profile, settings, privacy, and error states

**Files:**
- Create: `miniprogram/pages/notifications/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/pages/profile/index.{ts,wxml,wxss,json}`
- Create: `miniprogram/utils/errors.ts`
- Create: `docs/privacy-data-inventory.md`
- Create: `tests/unit/errors.test.ts`
- Create: `tests/e2e/profile-notifications.spec.ts`

**Interfaces:**
- Consumes: `listNotifications`, `markNotificationRead`, `clearNotifications`, `saveCategory`, `AppNotification`, and `CloudFailure` codes.
- Produces: notification center, profile/settings UI, consistent Chinese error messages, and an auditable data inventory.

- [ ] **Step 1: Write the failing error-mapping test.**

```ts
import { describe, expect, it } from 'vitest';
import { toUserMessage } from '../../miniprogram/utils/errors';

it('maps an ownership failure to a neutral Chinese message', () => {
  expect(toUserMessage('NOT_FOUND')).toBe('内容不存在或已被删除');
});
```

- [ ] **Step 2: Run the tests to verify error mapping and pages are absent.**

Run: `npx vitest run tests/unit/errors.test.ts tests/e2e/profile-notifications.spec.ts`

Expected: FAIL because `toUserMessage` and the pages do not exist.

- [ ] **Step 3: Implement error mapping and notification actions.**

```ts
// miniprogram/utils/errors.ts
export function toUserMessage(code: string): string {
  const messages: Record<string, string> = {
    VALIDATION_ERROR: '请检查填写内容',
    NOT_FOUND: '内容不存在或已被删除',
    FORBIDDEN: '无权执行此操作',
    CONFLICT: '当前内容无法这样修改',
    SUBSCRIPTION_REQUIRED: '任务已保存，但未开启微信提醒',
    UPLOAD_REJECTED: '仅支持 10MB 以内的图片或 PDF',
    INTERNAL_ERROR: '服务暂时不可用，请稍后重试',
  };
  return messages[code] ?? messages.INTERNAL_ERROR;
}
```

Notification page must group by today and earlier, mark an item read before navigating to `/pages/task-detail/index?id=${taskId}`, and confirm before `clearNotifications()`. Profile page must expose category management, reminder explanation, privacy policy, and a local-only `清除本地缓存` action using `wx.clearStorage()`; it must not imply that deleting cache deletes cloud data.

- [ ] **Step 4: Write the privacy data inventory.**

Create `docs/privacy-data-inventory.md` with this exact inventory table:

| Data | Purpose | Storage | Retention |
| --- | --- | --- | --- |
| WeChat OpenID | associate private records with the current user | CloudBase `users` | until user requests account deletion |
| task text, dates, category, priority, subtasks | task-management service | CloudBase `tasks` | until user deletes the task or account |
| image/PDF attachments | display task attachments | CloudBase storage | until task or account deletion |
| reminder delivery status | avoid duplicate notices and show in-app notification | CloudBase `reminderDeliveries`, `notifications` | until task deletion or 90 days after delivery |

- [ ] **Step 5: Run tests and verify clear-cache behavior manually.**

Run:

```powershell
npx vitest run tests/unit/errors.test.ts tests/e2e/profile-notifications.spec.ts
npx tsc --noEmit
```

Expected: PASS. Manually clear storage, relaunch, and verify cloud tasks reappear after bootstrap.

- [ ] **Step 6: Commit user-facing reliability and privacy surfaces.**

```powershell
git add miniprogram/pages miniprogram/utils docs/privacy-data-inventory.md tests
git commit -m "feat: add notifications profile and privacy handling"
```

### Task 11: Add release automation, real-device verification records, and review materials

**Files:**
- Create: `.github/workflows/quality.yml`
- Create: `docs/release-checklist.md`
- Create: `docs/wechat-review-script.md`
- Create: `tests/e2e/smoke.spec.ts`
- Modify: `package.json`

**Interfaces:**
- Consumes: all previous tests, CloudBase deployment configuration, and the final Mini Program build.
- Produces: repeatable quality gate, reviewer test script, privacy/release checklist, and a release candidate artifact.

- [ ] **Step 1: Write a failing smoke test for the final route set.**

```ts
import automator from 'miniprogram-automator';
import { expect, it } from 'vitest';

it('opens every primary MVP route without a render error', async () => {
  const miniProgram = await automator.launch({ projectPath: process.cwd() });
  for (const route of ['/pages/home/index', '/pages/calendar/index', '/pages/notifications/index', '/pages/profile/index']) {
    const page = await miniProgram.reLaunch(route);
    expect(await page.path()).toBe(route);
  }
  await miniProgram.close();
});
```

- [ ] **Step 2: Run the smoke test before wiring automation.**

Run: `npx vitest run tests/e2e/smoke.spec.ts`

Expected: FAIL until Developer Tools automation configuration and all four pages are present.

- [ ] **Step 3: Add the CI quality gate.**

```yaml
# .github/workflows/quality.yml
name: quality
on: [pull_request, push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npx vitest run tests/unit tests/cloudfunctions
```

Keep `miniprogram-automator` smoke tests in the real-device/Developer-Tools release gate when CI cannot launch the local WeChat IDE.

- [ ] **Step 4: Write the exact release checklist and reviewer journey.**

`docs/release-checklist.md` must require: production CloudBase environment selection; production `FLOWLIST_REMINDER_TEMPLATE_ID`; database indexes for `ownerOpenid + dueAtMs` and `ownerOpenid + updatedAtMs`; privacy-policy URL; customer-support contact; Android and iOS screenshots; development and production test accounts; a tested rollback build; and confirmation that no secret exists in repository history.

`docs/wechat-review-script.md` must tell reviewers to: open the Mini Program; create `审核任务` due ten minutes later; save it; view it in home and calendar; open details; complete it; inspect notification center; upload one PDF smaller than 10 MB; and open the privacy page. It must state that subscription-message behavior requires the reviewer to accept the WeChat prompt.

- [ ] **Step 5: Run the full quality gate and real-device release gate.**

Run:

```powershell
npx tsc --noEmit
npx vitest run tests/unit tests/cloudfunctions
npx vitest run tests/e2e/smoke.spec.ts
```

Expected: all automated tests PASS. Record Android and iOS verification results in the release checklist, including subscription acceptance, rejection, and notification tap behavior.

- [ ] **Step 6: Commit release readiness.**

```powershell
git add .github docs tests package.json package-lock.json
git commit -m "chore: add Flowlist release quality gates"
```

## Self-Review

### Spec coverage

- Welcome and WeChat identity: Task 3 and Task 7.
- Homepage task overview, search, filters, direct completion, and quick add: Task 4 and Task 7.
- Task detail, editing, subtasks, attachments, save, and confirmed deletion: Task 5 and Task 8.
- Create form fields, date-time, priority, category, and reminder: Tasks 2, 4, 7, and 9.
- Calendar month and selected-day tasks: Tasks 6 and 8.
- Notification center, read state, clear action, and detail navigation: Tasks 6 and 10.
- Profile, category management, reminder explanation, privacy: Tasks 3 and 10.
- Private data, authentication, CloudBase, tests, delivery, and review: Tasks 1, 3, 9, and 11.

No approved requirement is without an implementing task. The only conditional deliverable is WeChat subscription-message delivery; Task 9 contains a concrete platform gate and in-app-only downgrade path.

### Placeholder scan

The scan for unfinished markers found only the valid lowercase domain value `todo` in `TaskStatus`; it found no unfinished implementation marker. The plan contains no generic error-handling instruction, omitted user-facing error text, or unspecified cloud-function contract.

### Type consistency

- Task and reminder fields use `TaskInput`, `Task`, `Reminder`, `TaskPriority`, and `ReminderOffset` from Shared Interfaces throughout.
- All cloud calls return `CloudResult<T>` and are invoked through `callCloud<T>()`.
- `taskSave` accepts `SaveTaskInput`; `listTasks` accepts `TaskListInput`; notification methods use `AppNotification`.
- Reminder delivery uses `task.id`, `task.reminder.triggerAtMs`, and `ReminderStatus` consistently across Tasks 4, 6, and 9.

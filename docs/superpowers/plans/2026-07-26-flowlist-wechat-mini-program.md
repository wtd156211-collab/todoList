# Flowlist 鑷缓鍚庣寰俊灏忕▼搴忓疄鏂借鍒?
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** 浜や粯鍙湪寰俊涓櫥褰曘€佽法璁惧鍚屾涓汉浠诲姟銆佺鐞嗙鏈夐檮浠跺苟鎺ユ敹搴旂敤鍐呮彁閱掔殑 Flowlist 灏忕▼搴忎笌鑷缓 Python 鏈嶅姟绔€?
**Architecture:** 鍘熺敓寰俊灏忕▼搴忕粡 HTTPS 璋冪敤 Nginx 涓嬬殑 /flowlist/api/v1 FastAPI 鍗曚綋鏈嶅姟銆侾ostgreSQL 淇濆瓨鏁版嵁锛孯edis 鏀寔 Celery锛涢檮浠剁敱 API 绛惧彂鐭椂 OSS POST 琛ㄥ崟绛栫暐鐩翠紶绉佹湁 Bucket銆侱ocker Compose 閮ㄧ讲 API銆乄orker銆丅eat銆丳ostgreSQL 涓?Redis銆?
**Tech Stack:** TypeScript銆佸師鐢?WXML/WXSS銆丮obX Mini Program 6.12.3銆丗astAPI銆丼QLAlchemy 2銆丄lembic銆丳ostgreSQL 16銆丷edis 7銆丆elery銆侀樋閲屼簯 OSS Python SDK V2銆丏ocker Compose銆乸ytest銆乂itest銆?
## Global Constraints

- 浠呬氦浠樺井淇″皬绋嬪簭锛涗笉鍔犲叆 H5銆佸師鐢?App銆佸洟闃熷崗浣溿€佸叡浜换鍔℃垨浠樿垂鑳藉姏銆?- API 鍩鸿矾寰勫浐瀹氫负 /flowlist/api/v1锛涘仴搴锋鏌ヤ负 GET /flowlist/api/v1/health銆?- 鐢ㄦ埛韬唤鍙敱鏈嶅姟绔?Bearer token 鍐冲畾锛涘皬绋嬪簭涓嶅緱鎸佹湁 AppSecret銆丱SS AccessKey 鎴栨暟鎹簱鍑嵁銆?- OSS Bucket flowlist 淇濇寔绉佹湁锛屽璞￠敭鍥哄畾涓?flowlist/{user_id}/{task_id}/{uuid}锛涗粎 JPEG銆丳NG銆丳DF锛屽崟鏂囦欢鏈€澶?10 MiB銆佹瘡浠诲姟鏈€澶?5 涓€?- 鎵€鏈夋椂闂翠互 UTC 瀛樺偍锛屾柊鐢ㄦ埛鏃跺尯涓?Asia/Shanghai銆?- .env銆乸roject.private.config.json銆佷换浣?AccessKey 鎴?token 涓嶅緱鎻愪氦锛沺roject.config.json 搴旂撼鍏ヤ粨搴撱€?- 姣忛」浠诲姟鍏堝啓澶辫触娴嬭瘯锛屽悗浣滄渶灏忓疄鐜帮紱娴嬭瘯閫氳繃鍚庡崟鐙彁浜ゅ苟鎺ㄩ€?origin/master銆?
---

## 鏂囦欢缁撴瀯

    miniprogram/
      app.ts, app.json, app.wxss
      pages/{home,task-form,task-detail,calendar,notifications,profile}/
      components/{task-card,task-editor,month-calendar,empty-state}/
      services/{api,auth,tasks,categories,attachments,notifications}.ts
      stores/{session,tasks}.ts
    backend/
      app/{api,core,db,models,schemas,services,workers}/
      alembic/versions/
      tests/{unit,integration}/
    deploy/nginx/flowlist.conf
    compose.yaml

miniprogram/services 鏄〉闈㈣闂綉缁滅殑鍞竴鍏ュ彛銆傚悗绔?API 鍙鐞?HTTP锛宻ervices 鎵挎媴涓氬姟瑙勫垯锛宮odels 鍙〃绀烘寔涔呭寲銆侰elery Worker 璋冪敤鍚屼竴 service 灞傘€?
## 鍏变韩鎺ュ彛

    export type ApiResult<T> =
      | { ok: true; data: T }
      | { ok: false; code: 'AUTHENTICATION_FAILED' | 'VALIDATION_ERROR' | 'NOT_FOUND' | 'FORBIDDEN' | 'CONFLICT' | 'UPLOAD_REJECTED' | 'INTERNAL_ERROR'; message: string };

    export interface TaskInput {
      title: string; note: string; categoryId: string | null;
      priority: 'low' | 'medium' | 'high'; dueAt: string | null;
      timezone: string; reminderAt: string | null;
    }

    async def create_task(session: AsyncSession, user_id: UUID, payload: TaskCreate) -> Task: ...
    async def update_task(session: AsyncSession, user_id: UUID, task_id: UUID, version: int, payload: TaskUpdate) -> Task: ...
    async def create_upload_policy(session: AsyncSession, user_id: UUID, task_id: UUID, payload: AttachmentCreate) -> UploadPolicy: ...

### Task 1: 寤虹珛灏忕▼搴忋€丗astAPI 涓?Compose 楠ㄦ灦

**Files:**

- Create: .gitignore, package.json, tsconfig.json, vitest.config.ts, miniprogram/app.ts, miniprogram/app.json, miniprogram/app.wxss, backend/pyproject.toml, backend/app/main.py, backend/tests/unit/test_health.py, tests/unit/app-config.test.ts, compose.yaml, .env.example
- Modify: project.config.json
- Test: backend/tests/unit/test_health.py, tests/unit/app-config.test.ts

**Interfaces:** 寰俊寮€鍙戣€呭伐鍏峰彲鎵撳紑 miniprogram/锛孏ET /flowlist/api/v1/health 杩斿洖 status ok銆?
- [ ] **Step 1: 鍐欏け璐ユ祴璇曘€?*

    from fastapi.testclient import TestClient
    from app.main import app

    def test_health() -> None:
        response = TestClient(app).get('/flowlist/api/v1/health')
        assert response.json() == {'status': 'ok'}

    import config from '../../miniprogram/app.json';
    import { expect, it } from 'vitest';
    it('registers six MVP pages', () => expect(config.pages).toHaveLength(6));

- [ ] **Step 2: 杩愯澶辫触娴嬭瘯銆?*

Run: cd backend; uv run pytest tests/unit/test_health.py -q
Run: npm test -- tests/unit/app-config.test.ts
Expected: FAIL锛屾ā鍧楀皻涓嶅瓨鍦ㄣ€?
- [ ] **Step 3: 浣滄渶灏忓疄鐜般€?*

    from fastapi import FastAPI

    app = FastAPI(title='Flowlist API')

    @app.get('/flowlist/api/v1/health')
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

灏?project.config.json 鐨?miniprogramRoot 璁句负 miniprogram/銆傚浐瀹?mobx-miniprogram 6.12.3銆乵obx-miniprogram-bindings 6.0.0 鍜?Vitest锛汸ython 闄愬埗涓?>=3.12,<3.13 骞跺０鏄?FastAPI銆丼QLAlchemy銆丄lembic銆乤syncpg銆丆elery銆丷edis銆丳yJWT銆乭ttpx銆乷ss2銆乸ytest銆傚拷鐣?.env銆乸roject.private.config.json銆乶ode_modules/銆?venv/銆?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: npm install; npm test -- tests/unit/app-config.test.ts
Run: cd backend; uv sync; uv run pytest tests/unit/test_health.py -q
Expected: PASS銆?
    git add .gitignore package.json package-lock.json tsconfig.json vitest.config.ts project.config.json miniprogram backend compose.yaml .env.example tests
    git commit -m "chore: scaffold Flowlist mini program and API"
    git push origin master

### Task 2: 娣诲姞閰嶇疆銆侀敊璇崗璁笌 PostgreSQL 杩佺Щ

**Files:**

- Create: backend/app/core/config.py, backend/app/core/errors.py, backend/app/db/base.py, backend/app/db/session.py, backend/app/models/user.py, backend/app/models/category.py, backend/app/models/task.py, backend/app/models/attachment.py, backend/app/models/reminder.py, backend/app/models/notification.py, backend/alembic.ini, backend/alembic/env.py, backend/alembic/versions/0001_initial_schema.py, backend/tests/unit/test_config.py, backend/tests/integration/test_schema.py
- Modify: backend/app/main.py, compose.yaml, .env.example
- Test: backend/tests/unit/test_config.py, backend/tests/integration/test_schema.py

**Interfaces:** Settings銆侀敊璇?JSON {code,message,request_id,details?} 鍜?users/categories/tasks/task_attachments/reminders/notifications 琛ㄣ€?
- [ ] **Step 1: 鍐欏け璐ユ祴璇曘€?*

    def test_missing_database_url_is_rejected(monkeypatch):
        monkeypatch.delenv('DATABASE_URL', raising=False)
        with pytest.raises(ValidationError):
            Settings()

    async def test_task_has_version(session):
        task = Task(user_id=uuid4(), title='鏁寸悊璁″垝', priority='medium', status='todo', version=1)
        session.add(task)
        await session.flush()
        assert task.version == 1

- [ ] **Step 2: 纭澶辫触銆?*

Run: cd backend; uv run pytest tests/unit/test_config.py tests/integration/test_schema.py -q
Expected: FAIL锛岄厤缃拰妯″瀷灏氫笉瀛樺湪銆?
- [ ] **Step 3: 瀹炵幇閰嶇疆銆佹ā鍨嬪拰杩佺Щ銆?*

Settings 蹇呭～ DATABASE_URL銆丷EDIS_URL銆丣WT_SECRET銆乄ECHAT_APP_ID銆乄ECHAT_APP_SECRET銆丱SS_ENDPOINT銆丱SS_BUCKET銆丱SS_ACCESS_KEY_ID銆丱SS_ACCESS_KEY_SECRET锛屼笖涓嶅洖鏄惧€笺€備换鍔¤〃鍖呭惈 user/category銆佹爣棰樸€佹弿杩般€佷紭鍏堢骇銆佺姸鎬併€佹埅姝㈡椂闂淬€佹椂鍖恒€佸畬鎴愭椂闂淬€乿ersion 鍜屽璁℃椂闂淬€備负 user_id,due_at 鍙?user_id,updated_at 寤哄鍚堢储寮曘€侰ompose 鐨?PostgreSQL 鍜?Redis 涓嶅彂甯冨涓绘満绔彛銆?
- [ ] **Step 4: 杩佺Щ銆侀獙璇佸苟鎻愪氦銆?*

Run: docker compose up -d postgres redis
Run: cd backend; uv run alembic upgrade head; uv run pytest tests/unit/test_config.py tests/integration/test_schema.py -q
Expected: PASS銆?
    git add backend compose.yaml .env.example
    git commit -m "feat: add Flowlist data model and configuration"
    git push origin master

### Task 3: 瀹炵幇寰俊鐧诲綍鍜?Bearer 鎺堟潈

**Files:**

- Create: backend/app/api/auth.py, backend/app/core/security.py, backend/app/schemas/auth.py, backend/app/services/auth.py, backend/tests/integration/test_auth.py
- Modify: backend/app/main.py, backend/app/models/user.py
- Test: backend/tests/integration/test_auth.py

**Interfaces:** POST /auth/wechat-login銆丳OST /auth/refresh 鍜?get_current_user銆?
- [ ] **Step 1: 鍐欏け璐ユ祴璇曘€?*

    async def test_login_creates_user_and_returns_tokens(client, wechat_stub):
        response = await client.post('/flowlist/api/v1/auth/wechat-login', json={'code': 'wx-code'})
        assert response.status_code == 200
        assert response.json()['user']['openid'] == 'mock-openid'

    async def test_protected_route_rejects_missing_bearer(client):
        response = await client.get('/flowlist/api/v1/tasks')
        assert response.status_code == 401
        assert response.json()['code'] == 'AUTHENTICATION_FAILED'

- [ ] **Step 2: 纭澶辫触銆?*

Run: cd backend; uv run pytest tests/integration/test_auth.py -q
Expected: FAIL锛岃璇佺鐐瑰皻涓嶅瓨鍦ㄣ€?
- [ ] **Step 3: 瀹炵幇鐧诲綍鍜岀画鏈熴€?*

鐢?httpx 璋冨井淇?code2Session锛屾祴璇曚娇鐢?dependency override銆傛寜 OpenID get-or-create 鐢ㄦ埛锛涜闂?token 30 鍒嗛挓銆佸埛鏂?token 30 澶╋紝payload 浠呭惈 sub,type,exp,jti銆傛墍鏈夎姹傜敓鎴?X-Request-ID锛涙棩蹇椾笉寰楀惈 code銆乻ession_key銆乼oken 鎴?AppSecret銆?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: cd backend; uv run pytest tests/integration/test_auth.py -q
Expected: PASS銆?
    git add backend
    git commit -m "feat: add WeChat authentication and tokens"
    git push origin master

### Task 4: 瀹炵幇绉佹湁鍒嗙被鍜屼换鍔?CRUD

**Files:**

- Create: backend/app/api/categories.py, backend/app/api/tasks.py, backend/app/schemas/category.py, backend/app/schemas/task.py, backend/app/services/categories.py, backend/app/services/tasks.py, backend/tests/integration/test_tasks.py
- Modify: backend/app/main.py, backend/app/models/category.py, backend/app/models/task.py, backend/app/models/reminder.py
- Test: backend/tests/integration/test_tasks.py

**Interfaces:** 鍒嗙被 CRUD 鍜屼换鍔?list/create/read/update/complete/delete API銆傛洿鏂拌姹傚惈 version锛屾垚鍔熸椂鐗堟湰閫掑銆?
- [ ] **Step 1: 鍐欏け璐ョ殑褰掑睘涓庡啿绐佹祴璇曘€?*

    async def test_other_user_cannot_read_task(client, task_of_user_a, token_b):
        response = await client.get(f'/flowlist/api/v1/tasks/{task_of_user_a.id}', headers={'Authorization': f'Bearer {token_b}'})
        assert response.status_code == 404

    async def test_stale_version_returns_conflict(client, task, token):
        response = await client.patch(f'/flowlist/api/v1/tasks/{task.id}', json={'title': '鏂版爣棰?, 'version': 0}, headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 409

- [ ] **Step 2: 纭澶辫触銆?*

Run: cd backend; uv run pytest tests/integration/test_tasks.py -q
Expected: FAIL锛岀鐐瑰皻涓嶅瓨鍦ㄣ€?
- [ ] **Step 3: 瀹炵幇浠诲姟鍩熴€?*

鍒涘缓鐢ㄦ埛鏃剁敓鎴?Work 涓?Personal銆傚垪琛ㄦ敮鎸?scope=today|upcoming|all銆佸叧閿瘝銆佹棩鏈熴€佸垎绫汇€佺姸鎬佷笌鍒嗛〉銆傛瘡涓煡璇㈡樉寮忓姞鍏?Task.user_id == current_user.id銆傛洿鏂?SQL 浣跨敤 id銆乽ser_id銆乿ersion锛涙棤鍙楀奖鍝嶈鍒欒繑鍥?409銆備繚瀛樹换鍔″湪鍚屼竴浜嬪姟鍚屾鏂板缓銆佹洿鏂版垨鍙栨秷 reminder銆?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: cd backend; uv run pytest tests/integration/test_tasks.py -q
Expected: PASS锛岃秺鏉冩案杩滆繑鍥?404銆?
    git add backend
    git commit -m "feat: add private task and category APIs"
    git push origin master

### Task 5: 瀹炵幇绉佹湁 OSS 鐩翠紶鍜岄檮浠剁敓鍛藉懆鏈?
**Files:**

- Create: backend/app/api/attachments.py, backend/app/schemas/attachment.py, backend/app/services/attachments.py, backend/tests/unit/test_attachments.py, backend/tests/integration/test_attachment_api.py
- Modify: backend/app/main.py, backend/app/models/attachment.py
- Test: backend/tests/unit/test_attachments.py, backend/tests/integration/test_attachment_api.py

**Interfaces:** POST /tasks/{task_id}/attachments/upload-policy锛孭OST /attachments/{attachment_id}/confirm锛孏ET /attachments/{attachment_id}/download-url锛孌ELETE /attachments/{attachment_id}銆?
- [ ] **Step 1: 鍐欏け璐ユ祴璇曘€?*

    def test_object_key_is_user_and_task_scoped():
        key = build_object_key(UUID('00000000-0000-0000-0000-000000000001'), UUID('00000000-0000-0000-0000-000000000002'))
        assert key.startswith('flowlist/00000000-0000-0000-0000-000000000001/00000000-0000-0000-0000-000000000002/')

    async def test_upload_policy_requires_task_ownership(client, token_b, task_of_user_a):
        response = await client.post(f'/flowlist/api/v1/tasks/{task_of_user_a.id}/attachments/upload-policy', json={'filename':'a.pdf','mimeType':'application/pdf','sizeBytes':20}, headers={'Authorization': f'Bearer {token_b}'})
        assert response.status_code == 404

- [ ] **Step 2: 纭澶辫触銆?*

Run: cd backend; uv run pytest tests/unit/test_attachments.py tests/integration/test_attachment_api.py -q
Expected: FAIL銆?
- [ ] **Step 3: 瀹炵幇绛惧彂涓庣‘璁ゃ€?*

鏍￠獙 MIME銆?0 MiB 鍜?5 涓檮浠朵笂闄愩€傜鍙戜粎璇ュ璞″彲鐢ㄣ€?0 鍒嗛挓杩囨湡鐨?OSS POST policy锛涚‘璁ゆ椂浣跨敤鍙浛鎹?OSS client 鐨?head_object 鏍￠獙瀵硅薄瀛樺湪涓庡ぇ灏忋€備笅杞界鍚?5 鍒嗛挓锛涘垹闄ゆ暟鎹簱璁板綍鍚庢姇閫掑彲閲嶈瘯 OSS 鍒犻櫎浠诲姟銆傝嚜鍔ㄦ祴璇曚笉寰椾娇鐢ㄧ湡瀹?OSS 瀵嗛挜銆?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: cd backend; uv run pytest tests/unit/test_attachments.py tests/integration/test_attachment_api.py -q
Expected: PASS銆?
    git add backend
    git commit -m "feat: add private OSS attachment uploads"
    git push origin master

### Task 6: 瀹炵幇鎻愰啋銆侀€氱煡鍜?Celery 璋冨害

**Files:**

- Create: backend/app/api/notifications.py, backend/app/services/reminders.py, backend/app/workers/celery_app.py, backend/app/workers/tasks.py, backend/tests/unit/test_reminders.py, backend/tests/integration/test_notifications.py
- Modify: backend/app/models/reminder.py, backend/app/models/notification.py, compose.yaml
- Test: backend/tests/unit/test_reminders.py, backend/tests/integration/test_notifications.py

**Interfaces:** GET /notifications銆丳ATCH /notifications/{id}/read銆丏ELETE /notifications 鍜屽箓绛?deliver_due_reminders銆?
- [ ] **Step 1: 鍐欏け璐ュ箓绛夋祴璇曘€?*

    async def test_due_reminder_creates_one_notification_once(session, due_reminder):
        first = await deliver_due_reminders(session, now=due_reminder.remind_at)
        second = await deliver_due_reminders(session, now=due_reminder.remind_at)
        assert first.created_count == 1
        assert second.created_count == 0

- [ ] **Step 2: 纭澶辫触銆?*

Run: cd backend; uv run pytest tests/unit/test_reminders.py tests/integration/test_notifications.py -q
Expected: FAIL銆?
- [ ] **Step 3: 瀹炵幇 Worker銆?*

Beat 姣忓垎閽熸姇閫掋€俉orker 鍘熷瓙鍦板皢 pending reminder 璁ら涓?processing锛涙垚鍔熸椂鍐欓€氱煡骞惰 sent锛屽紓甯稿鍔?attempts 骞惰 failed锛屾渶澶?3 娆°€傞€氱煡鎵€鏈夋搷浣滄寜 user_id 杩囨护銆傚閮ㄨ闃呮秷鎭粎淇濈暀 feature flag锛屼笉鍙栧緱妯℃澘鍜岀敤鎴锋巿鏉冩椂涓嶅彂閫併€?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: cd backend; uv run pytest tests/unit/test_reminders.py tests/integration/test_notifications.py -q
Run: docker compose up -d worker beat; docker compose ps
Expected: PASS锛寃orker 涓?beat running銆?
    git add backend compose.yaml
    git commit -m "feat: add task reminders and notifications"
    git push origin master

### Task 7: 瀹炵幇灏忕▼搴?API 瀹㈡埛绔€佷細璇濆拰 MobX 鐘舵€?
**Files:**

- Create: miniprogram/services/api.ts, miniprogram/services/auth.ts, miniprogram/services/tasks.ts, miniprogram/services/categories.ts, miniprogram/services/attachments.ts, miniprogram/services/notifications.ts, miniprogram/stores/session.ts, miniprogram/stores/tasks.ts, miniprogram/utils/errors.ts, miniprogram/utils/storage.ts, miniprogram/config.ts, tests/unit/api.test.ts, tests/unit/session.test.ts, tests/unit/tasks-store.test.ts
- Modify: miniprogram/app.ts
- Test: tests/unit/api.test.ts, tests/unit/session.test.ts, tests/unit/tasks-store.test.ts

**Interfaces:** request<T>銆乪nsureSession 鍜?taskStore.refresh銆?
- [ ] **Step 1: 鍐欏け璐ョ殑 401 閲嶇櫥娴嬭瘯銆?*

    it('retries exactly once after 401', async () => {
      mockRequest.mockResolvedValueOnce({ statusCode: 401 }).mockResolvedValueOnce({ statusCode: 200, data: { items: [] } });
      await expect(request('/tasks', { method: 'GET' })).resolves.toEqual({ ok: true, data: { items: [] } });
      expect(mockLogin).toHaveBeenCalledTimes(1);
    });

- [ ] **Step 2: 纭澶辫触銆?*

Run: npm test -- tests/unit/api.test.ts tests/unit/session.test.ts tests/unit/tasks-store.test.ts
Expected: FAIL銆?
- [ ] **Step 3: 瀹炵幇浼氳瘽灞傘€?*

ensureSession 鐢?wx.login 璋冪櫥褰?API锛屽皢 token 鍐欏叆鏈湴 storage銆傛瘡娆?request 杩藉姞 Bearer token锛?01 鏃舵竻闄?token銆侀噸鏂扮櫥褰曘€佷粎閲嶈瘯鍘熻姹備竴娆°€俠ase URL 鍐欏湪涓嶅惈鏈哄瘑鐨?config.ts锛屽舰濡?https://浣犵殑鍩熷悕/flowlist/api/v1锛岄儴缃插墠鏇挎崲銆傞〉闈笉寰楃洿鎺?wx.request銆?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: npm test -- tests/unit/api.test.ts tests/unit/session.test.ts tests/unit/tasks-store.test.ts
Expected: PASS銆?
    git add miniprogram tests package.json package-lock.json
    git commit -m "feat: add mini program session and API client"
    git push origin master

### Task 8: 瀹炵幇棣栭〉銆佷换鍔＄紪杈戝拰璇︽儏

**Files:**

- Create: miniprogram/pages/home/index.ts, miniprogram/pages/home/index.wxml, miniprogram/pages/home/index.wxss, miniprogram/pages/home/index.json, miniprogram/pages/task-form/index.ts, miniprogram/pages/task-form/index.wxml, miniprogram/pages/task-form/index.wxss, miniprogram/pages/task-form/index.json, miniprogram/pages/task-detail/index.ts, miniprogram/pages/task-detail/index.wxml, miniprogram/pages/task-detail/index.wxss, miniprogram/pages/task-detail/index.json, miniprogram/components/task-card/index.ts, miniprogram/components/task-card/index.wxml, miniprogram/components/task-card/index.wxss, miniprogram/components/task-card/index.json, miniprogram/components/task-editor/index.ts, miniprogram/components/task-editor/index.wxml, miniprogram/components/task-editor/index.wxss, miniprogram/components/task-editor/index.json, tests/unit/task-editor.test.ts
- Test: tests/unit/task-editor.test.ts

**Interfaces:** validateTaskDraft銆佷换鍔″崱鐗?toggle/open 浜嬩欢銆佺紪杈戝櫒 TaskInput 鍜?version銆?
- [ ] **Step 1: 鍐欏け璐ヨ〃鍗曟祴璇曘€?*

    import { validateTaskDraft } from '../../miniprogram/components/task-editor/index';
    it('requires a non-blank title', () => expect(validateTaskDraft({ title: '   ' } as never)).toBe('璇疯緭鍏ヤ换鍔℃爣棰?));

- [ ] **Step 2: 纭澶辫触銆?*

Run: npm test -- tests/unit/task-editor.test.ts
Expected: FAIL銆?
- [ ] **Step 3: 瀹炵幇鏍稿績 UI銆?*

棣栭〉鏈変粖鏃?鍗冲皢鍒版湡/鍏ㄩ儴绛涢€夈€佹悳绱€佸畬鎴愬紑鍏冲拰鏂板鍏ュ彛銆傜紪杈戝櫒鏀寔鏍囬銆佹弿杩般€佸垎绫汇€佷紭鍏堢骇銆佹埅姝㈡椂闂村拰鎻愰啋銆傝鎯呴〉鍔犺浇 id锛屾樉绀洪檮浠讹紱409 鏄剧ず鈥滀换鍔″凡鍦ㄥ叾浠栬澶囦慨鏀癸紝璇峰埛鏂板悗閲嶈瘯鈥濓紱鍒犻櫎浣跨敤 wx.showModal 浜屾纭銆?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: npm test -- tests/unit/task-editor.test.ts
Run: npx tsc --noEmit
Expected: PASS锛涘紑鍙戣€呭伐鍏峰彲杩涘叆杩欎笁涓〉闈€?
    git add miniprogram tests
    git commit -m "feat: add task list editor and details UI"
    git push origin master

### Task 9: 瀹炵幇鏃ュ巻銆侀檮浠躲€侀€氱煡鍜屼釜浜鸿缃?
**Files:**

- Create: miniprogram/pages/calendar/index.ts, miniprogram/pages/calendar/index.wxml, miniprogram/pages/calendar/index.wxss, miniprogram/pages/calendar/index.json, miniprogram/pages/notifications/index.ts, miniprogram/pages/notifications/index.wxml, miniprogram/pages/notifications/index.wxss, miniprogram/pages/notifications/index.json, miniprogram/pages/profile/index.ts, miniprogram/pages/profile/index.wxml, miniprogram/pages/profile/index.wxss, miniprogram/pages/profile/index.json, miniprogram/pages/settings/categories/index.ts, miniprogram/pages/settings/categories/index.wxml, miniprogram/pages/settings/categories/index.wxss, miniprogram/pages/settings/categories/index.json, miniprogram/components/month-calendar/index.ts, miniprogram/components/month-calendar/index.wxml, miniprogram/components/month-calendar/index.wxss, miniprogram/components/month-calendar/index.json, miniprogram/components/empty-state/index.ts, miniprogram/components/empty-state/index.wxml, miniprogram/components/empty-state/index.wxss, miniprogram/components/empty-state/index.json, tests/unit/month-calendar.test.ts, tests/unit/errors.test.ts, docs/privacy-data-inventory.md
- Modify: miniprogram/pages/task-form/index.ts, miniprogram/pages/task-detail/index.ts
- Test: tests/unit/month-calendar.test.ts, tests/unit/errors.test.ts

**Interfaces:** buildTaskDateSet銆乽ploadAttachment 鍜?toUserMessage銆?
- [ ] **Step 1: 鍐欏け璐ョ殑鏃ュ巻涓庨敊璇槧灏勬祴璇曘€?*

    it('marks dates containing due tasks', () => {
      expect(buildTaskDateSet([{ dueAt: '2026-07-26T00:00:00Z' }], 'Asia/Shanghai')).has('2026-07-26')).toBe(true);
    });
    it('maps missing task to Chinese copy', () => expect(toUserMessage('NOT_FOUND')).toBe('鍐呭涓嶅瓨鍦ㄦ垨宸茶鍒犻櫎'));

- [ ] **Step 2: 纭澶辫触銆?*

Run: npm test -- tests/unit/month-calendar.test.ts tests/unit/errors.test.ts
Expected: FAIL銆?
- [ ] **Step 3: 瀹炵幇椤甸潰鍜屼笂浼犮€?*

鏃ュ巻閫夋嫨鏃ユ湡鍚庡鐢?task store銆傚浘鐗囩敤 wx.chooseMedia锛孭DF 鐢?wx.chooseMessageFile锛涘厛鎷?policy锛屼娇鐢?wx.uploadFile POST 鍒?OSS锛屽啀璋冪敤 confirm API銆傞€氱煡鍙爣宸茶銆佹墦寮€璇︽儏銆佺‘璁ゆ竻绌恒€備釜浜洪〉鍙鐞嗗垎绫汇€佹煡鐪嬫彁閱掑拰闅愮璇存槑銆佸彧娓呮湰鍦扮紦瀛樸€?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: npm test -- tests/unit/month-calendar.test.ts tests/unit/errors.test.ts
Run: npx tsc --noEmit
Expected: PASS銆?
    git add miniprogram tests docs/privacy-data-inventory.md
    git commit -m "feat: add calendar attachments and settings UI"
    git push origin master

### Task 10: 娣诲姞鐢熶骇閮ㄧ讲銆佽川閲忛棬绂佸拰鐪熸満楠屾敹

**Files:**

- Create: deploy/nginx/flowlist.conf, docs/deployment.md, docs/release-checklist.md, docs/wechat-review-script.md, .github/workflows/quality.yml, backend/tests/integration/test_deployment_contract.py
- Modify: compose.yaml, .env.example, README.md
- Test: backend/tests/integration/test_deployment_contract.py

**Interfaces:** Nginx 鍙浆鍙?/flowlist/api/v1/锛孏itHub Actions 杩愯鍚庣鍜屽墠绔祴璇曘€?
- [ ] **Step 1: 鍐欏け璐ラ儴缃茶矾鐢辨祴璇曘€?*

    def test_nginx_keeps_flowlist_path_prefix():
        config = Path('deploy/nginx/flowlist.conf').read_text(encoding='utf-8')
        assert 'location /flowlist/api/v1/' in config
        assert 'proxy_pass http://flowlist-api:8000;' in config

- [ ] **Step 2: 纭澶辫触銆?*

Run: cd backend; uv run pytest tests/integration/test_deployment_contract.py -q
Expected: FAIL銆?
- [ ] **Step 3: 瀹炵幇閮ㄧ讲鏉愭枡銆?*

Nginx 浠呬唬鐞?/flowlist/api/v1/ 鑷?flowlist-api:8000銆傞儴缃叉枃妗ｅ寘鍚湇鍔″櫒绉佹湁 .env銆佹墜宸ュ～ RAM AccessKey銆乥uild/up銆丄lembic銆佸仴搴锋鏌ャ€佹棩蹇椼€佸浠藉拰鍥炴粴銆侰I 杩愯 npm ci銆乶pm test銆乽v sync --frozen 鍜?pytest銆傛竻鍗曡姹傚井淇″悗鍙?request/uploadFile/downloadFile HTTPS 鍩熷悕銆丄ndroid/iOS 鐪熸満楠岃瘉鍜屽瘑閽ユ壂鎻忋€?
- [ ] **Step 4: 楠岃瘉骞舵彁浜ゃ€?*

Run: npm test
Run: npx tsc --noEmit
Run: cd backend; uv run pytest -q
Run: docker compose config
Expected: 鍏ㄩ儴 PASS銆?
    git add deploy docs .github compose.yaml .env.example README.md backend
    git commit -m "chore: add Flowlist deployment and release checks"
    git push origin master

## 鑷

- 浠诲姟 3鈥?0 瑕嗙洊鐧诲綍銆佷换鍔°€佸垎绫汇€佺鏈?OSS銆佹彁閱掋€佹棩鍘嗐€侀€氱煡銆佽缃€侀儴缃蹭笌楠屾敹銆?- 姣忛」鍧囧寘鍚け璐ユ祴璇曘€佹渶灏忓疄鐜般€侀€氳繃楠岃瘉銆佺嫭绔?Git 鎻愪氦鍜屾帹閫併€?- 鍞竴闇€瑕佺敤鎴峰湪閮ㄧ讲闃舵濉啓鐨勪俊鎭槸鍩熷悕鍜屾満瀵嗭紱瀹冧滑琚槑纭檺鍒跺湪鏈嶅姟鍣?.env 鎴栧井淇″悗鍙帮紝闈炰唬鐮佺己椤广€?

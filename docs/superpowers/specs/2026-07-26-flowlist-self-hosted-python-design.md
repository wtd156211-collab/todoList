# Flowlist 自建 Python 后端设计说明

## 目标与范围

Flowlist 首版是面向单个用户的微信个人任务管理小程序。用户可以使用微信登录，创建、编辑、完成和筛选任务，按日历查看任务，为任务添加附件，并在到期前接收提醒。首版不提供团队、共享任务、多人协作、付费或管理后台。

任务数据需要跨设备同步；附件存入阿里云 OSS，而不是应用服务器磁盘。用户已创建私有 Bucket `flowlist`（华北 2/北京）及仅能访问 `flowlist/` 前缀的 RAM 用户 `flowlist-server`。

## 总体架构

小程序使用 TypeScript、原生 WXML/WXSS 和 MobX。它通过 HTTPS 调用同一已存在域名下的 `/flowlist/api/v1/` 路由；该路由由 Nginx 转发给 FastAPI。服务端以 Docker Compose 部署为一个单体应用：FastAPI API、PostgreSQL、Redis、Celery Worker 和 Celery Beat。该边界在首版足够清晰，并避免微服务带来的额外运维成本。

```text
微信小程序
  ├── HTTPS API ──> Nginx ──> FastAPI ──> PostgreSQL
  └── POST 表单临时凭证 ──> 私有阿里云 OSS

FastAPI ──> Redis ──> Celery Worker / Celery Beat ──> 到期提醒
```

Nginx 只负责 TLS 终止和路径转发；应用只处理 `/flowlist/api/v1` 下的业务请求，不能影响同域名的既有小程序。Compose 服务只暴露 Nginx 所需端口，PostgreSQL 和 Redis 不对公网开放。

## 客户端模块与 API 边界

客户端包含：首页任务列表、任务新建/详情、日历、通知中心、个人设置。全局状态只保存当前用户、访问令牌、分类和短期任务缓存；PostgreSQL 是任务数据的唯一事实来源。页面不直接访问数据库，也不持有任何微信 AppSecret 或 OSS AccessKey。

FastAPI 按领域划分为 `auth`、`tasks`、`categories`、`attachments`、`reminders`、`users` 模块。所有业务接口均位于 `/flowlist/api/v1`，使用 JSON，除健康检查外必须带 `Authorization: Bearer <token>`。响应使用统一错误结构：`code`、`message`、`request_id` 和可选 `details`。接口对无效输入返回 422、未登录返回 401、越权返回 403、缺失资源返回 404、并发修改冲突返回 409。

## 登录、权限与数据模型

小程序调用 `wx.login()` 获得临时 code，提交到 `POST /auth/wechat-login`。FastAPI 使用服务端环境变量中的微信 AppID/AppSecret 与微信接口交换 OpenID；创建或更新本地 `users` 记录后签发短期访问令牌与可续期令牌。AppSecret、会话密钥、OSS AccessKey 均仅存在服务器 `.env`；`.env` 永不提交。

核心表如下：

- `users`：`id`、`wechat_openid`、昵称、头像、时区、提醒设置。
- `categories`：`id`、`user_id`、名称、颜色、排序。
- `tasks`：`id`、`user_id`、`category_id`、标题、描述、优先级、状态、截止时间、完成时间、版本号与审计时间戳。
- `task_attachments`：`id`、`task_id`、OSS 对象键、原始文件名、MIME 类型、大小、上传状态。
- `reminders`：`id`、`task_id`、提醒时间、状态、尝试次数、最后错误。
- `device_subscriptions`：用户的订阅消息授权状态与更新时间。

查询、更新和删除都以令牌中的本地 `user_id` 作为强制过滤条件；客户端传来的用户标识不作为授权依据。

## 附件与提醒数据流

创建附件时，小程序先请求 API 创建附件记录及短时 OSS POST 表单策略。后端生成无法猜测的对象键 `flowlist/{user_id}/{task_id}/{uuid}`，校验用户确实拥有该任务，并把策略限制为该对象、允许的 MIME 类型与大小。小程序使用 `wx.uploadFile` 直传私有 OSS；上传成功后调用 API 确认，服务端将附件标记为可用。下载时客户端向 API 请求短时签名 URL，不能保存或展示永久公开地址。删除任务或附件会先删除数据库关联，再由后台删除对应 OSS 对象并记录失败以便重试。

用户创建或修改任务时，服务端在同一事务中写入任务和提醒记录。Celery Beat 定期查找待执行提醒并投递给 Worker；Worker 写入通知中心记录，并仅在用户已授权微信订阅消息、模板和平台条件均满足时发送订阅消息。未授权、模板不可用或发送失败不会阻塞任务保存，失败会记录为可重试状态。

## 部署、配置与可观测性

部署仓库提供 `docker-compose.yml`、生产覆盖配置、Nginx 站点片段、数据库迁移命令和 `.env.example`。生产 `.env` 由用户在 Ubuntu 22.04 服务器手动创建，包含数据库密码、JWT 密钥、微信凭据、OSS endpoint、Bucket、RAM AccessKey ID 与 Secret。应用启动时校验必填配置但绝不回显机密。

健康检查接口为 `GET /flowlist/api/v1/health`，不返回敏感信息。Nginx、API、Worker 使用结构化日志并携带 `request_id`；接口失败、OSS 确认失败和提醒失败均可据此追踪。备份范围包括 PostgreSQL 定期逻辑备份和 OSS 生命周期/恢复策略；Redis 不作为唯一持久数据来源。

## 错误处理与验收测试

后端单元测试覆盖令牌解析、任务归属校验、截止时间与状态转换、对象键生成和配置校验。API 集成测试覆盖微信登录交换的 mock、任务 CRUD、跨用户拒绝访问、分类筛选、附件签发/确认、下载签名和提醒创建。Celery 测试使用可控时间与假队列，验证提醒只投递一次及失败重试。

小程序测试覆盖 API 客户端错误映射、任务表单校验、列表/日历状态映射与附件上传状态。手工验收覆盖：真机微信登录、网络断开后的可读错误、任务跨设备同步、私有附件不能通过永久 URL 访问、用户拒绝订阅消息时任务仍正常保存，以及同域名既有小程序不受 `/flowlist/` 路由影响。

## 明确约束

- 小程序、FastAPI 和 OSS 仅使用 HTTPS；在微信后台分别配置 `request`、`uploadFile` 与 `downloadFile` 合法域名。
- OSS Bucket 保持私有并启用阻止公共访问；禁止 `public-read` 和 `public-read-write`。
- RAM 用户仅使用 `FlowlistOssObjectAccess`，不授予 `AliyunOSSFullAccess`、RAM 或 ECS 权限。
- 每个可独立验证的开发功能完成后执行测试、提交 Git，并推送至 `origin/master`。

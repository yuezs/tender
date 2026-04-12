# 开发任务状态

本文档记录当前项目的真实进度。

## 已完成

### 1. 项目骨架

- 已初始化 `frontend`，使用 Next.js + TypeScript。
- 已初始化 `backend`，使用 FastAPI。
- 已按模块划分后端目录结构。
- 已提供统一 JSON 返回结构。
- 已提供 `/api/health`。

### 2. 招标处理主链路 MVP

- 已支持招标文件上传。
- 已支持本地文件存储。
- 已支持 `txt / docx` 文本解析。
- 已提供 `/api/tender/parse`。
- 已提供 `/api/tender/extract`。
- 已提供 `/api/tender/judge`。
- 已提供 `/api/tender/generate`。
- 已完成前后端最小联调。

### 3. 简易知识库第一版

- 已创建 `knowledge_documents`。
- 已创建 `knowledge_chunks`。
- 已支持知识文档上传、列表、处理和简单检索。
- 已将知识片段接入 `judge_agent` 和 `generate_agent`。

### 4. OpenClaw Gateway 接入

- 已将 `extract / judge / generate` 从本地 CLI 子进程切到 OpenClaw Gateway WebSocket RPC。
- 已支持 `input.json / status.json / output.json` 产物落地。
- 已支持最小成功复用和失败兜底。
- 已补齐 `device identity` 握手及 token 读取。
- 已补齐 device token 持久化、token 失配自动清理与重连，降低 Gateway 缓存失效导致的连接失败。

### 5. 项目发现前置层

- 已新增 discovery 模块，支持手动触发 `ggzy` 项目采集。
- 已新增 `project_discovery_runs` 和 `project_leads` 两张表。
- 已新增 `/api/discovery/status`、`/api/discovery/runs`、`/api/discovery/projects`、`/api/discovery/projects/{lead_id}`。
- 已新增前端 `/discovery` 列表页和 `/discovery/[leadId]` 详情页。
- 已将项目发现入口加入首页和侧边导航。
- 已接入 `collect_agent`，并注册 `tender-collect` OpenClaw agent。
- 已补充 `keyword` 采集模式，支持 `keywords / regions / notice_types / exclude_keywords`。
- 已支持在 discovery 列表中展示 `matched_keywords`，用于说明线索命中原因。

### 6. 工作台演示版视觉升级

- 已统一前端全局 token、圆角、阴影、边框和中性色层级。
- 已升级共享组件：页面头部、面板卡片、指标卡、弹窗、侧边导航、空状态、状态时间线。
- 已完成 `/tender`、`/discovery`、`/results` 三个核心页面的工作台化演示版改造。
- 已减少卡片层级和面板套面板感，强化首屏焦点、摘要区和主操作入口。

### 7. discovery 120 秒控制与超时修复

- 已将 `ggzy` 采集默认候选数收敛到 `5`。
- 已将单次页面请求默认超时收敛到 `8s`。
- 已新增内部采集预算 `95s`，只返回预算内抓取完成的项目。
- 已将 `detail_text` 默认截断到 `2000` 字，降低会话收尾压力。
- 已修复 `agent.wait` 超时后仍可从 session 回收结果的问题，避免 OpenClaw UI 已有返回但后端误判失败。
- 已实测通过 `openclaw-agent` 跑通 discovery 采集，成功 run 可见 `provider = openclaw-gateway` 且 `used_fallback = false`。

## 当前仍是 MVP / 边界控制

- discovery 当前只支持 `ggzy` 单站手动采集。
- discovery 不下载附件，不解析附件，不自动进入写标书主链路。
- discovery 推荐逻辑当前基于规则评分加知识库命中，不新增独立评分 agent。
- discovery 关键词采集第一版仍不做自动补全、历史联想、常用策略保存和复杂同义词扩展。
- 招标文件 `pdf` 真实解析仍未补齐。
- 知识库前端管理能力仍较轻量。
- 当前主链路与 discovery 记录仍主要以本地文件和 MySQL 组合保存，不做复杂工作流。

## 下一阶段任务

### 1. discovery

- 继续验证关键词采集在不同关键词质量下的结果稳定性。
- 评估是否增加更多公开站点，但保持单次迭代可控。
- 增加 discovery 到主链路的明确人工确认入口，而不是自动推进。

### 2. 招标文件能力

- 补齐 `pdf` 真正解析能力。
- 评估是否需要 OCR。

### 3. 知识库

- 完善资料中心页面。
- 增加文档详情和片段预览。

### 4. 工程质量

- 增加接口测试。
- 增加关键流程回归测试。
- 增加更多日志和排障说明。

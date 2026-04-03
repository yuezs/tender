# 技术架构设计

本文档描述当前仓库的实际实现状态，而不是未来预研架构。

## 一、整体架构

```text
Frontend (Next.js + TypeScript + Tailwind)
        |
        v
Backend API (FastAPI)
        |
        +-- Discovery Module
        |     |
        |     +-- Knowledge-driven profile builder
        |     +-- collect_agent -> OpenClaw Gateway
        |     +-- Lead repository (MySQL + Local Storage)
        |
        +-- Tender Module
        |     |
        |     +-- Files Module
        |     +-- Agent Module
        |            |
        |            +-- OpenClaw Gateway Client (WebSocket RPC)
        |
        +-- Knowledge Module
        |
        +-- Core
              |
              +-- MySQL
              +-- Local Storage
              +-- Local OpenClaw Gateway
```

## 二、当前模块职责

### 1. frontend

职责：

- 提供工作台页面
- 上传招标文件
- 展示解析结果
- 展示投标建议
- 展示标书初稿
- 资料中心：上传企业资料、处理并调试检索
- 展示知识引用结果

当前页面：

- `/`
- `/discovery`
- `/discovery/{leadId}`
- `/tender`
- `/results`
- `/knowledge`

### 2. backend

职责：

- 提供统一 API 入口
- 编排招标主链路
- 编排知识库处理与检索
- 对接 Agent 调用链路
- 返回统一 JSON 结构
- 处理异常并输出可读错误信息

当前后端强制分层：

- `api/router`
- `service`
- `repository`
- `schema`
- `model`
- `core`

### 3. files 模块

职责：

- 保存上传文件到本地 `storage/`
- 解析招标文件文本
- 生成解析文本文件

当前状态：

- 已支持 `txt / docx`
- `pdf` 仅预留

### 4. tender 模块

职责：

- 管理招标文件处理主链路
- 驱动 `upload -> parse -> extract -> judge -> generate`
- 保存招标处理记录

当前状态：

- 当前记录先保存在本地 JSON
- 这样做是为了不被数据库建模阻塞 MVP 主链路
- 后续可以迁移到 MySQL

### 5. knowledge 模块

职责：

- 上传企业知识文档
- 解析文本
- 规则切块
- 写入 MySQL
- 提供简单检索能力
- 提供全文查看、原文件下载、删除能力

前端资料中心：

- `/knowledge` 页面提供上传、列表、处理、检索调试，用于验证知识入库与命中情况
- 当前页面还提供：
  - 最近处理结果（解析摘要 / 告警 / 重点内容 / 切块预览）
  - 文档操作下拉菜单（处理 / 全文查看 / 文件下载 / 删除）
  - 检索结果三行预览与弹窗全文查看

当前状态：

- `knowledge_documents` 和 `knowledge_chunks` 已落 MySQL
- 原文件落盘到 `storage/knowledge/raw/`
- 解析文本落盘到 `storage/knowledge/parsed/`
- 不使用 PostgreSQL
- 不使用 JSONB
- 不使用向量检索
- 当前知识文档仅支持 `txt / docx`
- `txt / docx` 会先解析为结构块，再进行规则切块
- `docx` 解析已支持段落、标题、列表、表格顺序读取
- 已支持段内编号标题识别与长段再切分
- 5 类资料均已支持规则版重点内容提取：`company_profile / business_info / qualifications / templates / project_cases`
- `process` 接口当前会返回：
  - `parse_summary`
  - `warnings`
  - `key_points`
  - `chunk_preview`
- 当前知识库接口包括：
  - `/api/knowledge/status`
  - `/api/knowledge/documents/upload`
  - `/api/knowledge/documents`
  - `/api/knowledge/documents/{document_id}/process`
  - `/api/knowledge/documents/{document_id}/content`
  - `/api/knowledge/documents/{document_id}/download`
  - `DELETE /api/knowledge/documents/{document_id}`
  - `/api/knowledge/retrieve`

### 6. agent 模块

职责：

- 维护 Prompt 模板
- 驱动 `collect_agent`
- 编排知识上下文
- 驱动 `extract_agent / judge_agent / generate_agent`
- 通过本地 OpenClaw Gateway 发起同步 Agent RPC
- 对模型输出做结构化校验

当前状态：

- 当前只保留 5 个 Agent：
  - `collect_agent`
  - `extract_agent`
  - `judge_agent`
  - `generate_agent`
  - `orchestrator`
- 对外 API 结构保持不变
- 内部真实调用路径已切换为本地 OpenClaw Gateway
- Gateway 握手已补齐本机 `device identity` 与设备 token
- Agent 会话 key 采用 `agent:<agent_id>:tender:<file_id>:<step>` 形式
- `extract / judge / generate` 强制走本地 OpenClaw Gateway，失败直接返回错误
- `collect_agent` 也强制走本地 OpenClaw Gateway，失败直接返回错误
- 知识检索与上下文组装是真实链路

### 7. discovery 模块

职责：

- 基于知识库构建企业能力画像
- 生成推荐采集方向
- 发起 `ggzy` 单站定向采集或广泛采集
- 保存采集记录、线索池和匹配结果
- 对项目做“方向命中 + 知识支撑”双层解释

当前状态：

- 新增 `/api/discovery/profile`，返回当前企业能力画像和推荐方向
- `POST /api/discovery/runs` 已支持 `mode / profile_key / keywords / regions / qualification_terms / industry_terms`
- `collect_agent` 优先通过本地 OpenClaw Gateway 执行，失败时回退到本地 `ggzy collector`
- 广泛采集当前直接接入全国公共资源交易平台“交易公开”公开列表接口，按 `0101 / 0201` 公告池多页抓取，单次默认可落库 120 条线索
- 定向匹配中的地区当前作为加分项保留，不再作为硬过滤条件
- discovery 列表排序规则已调整为：
  1. `recommendation_score desc`
  2. `targeting_match_score desc`
  3. `published_at desc`
- 定向采集参数会写入：
  - `project_discovery_runs.targeting_snapshot`
  - `storage/discovery/agent_runs/<run_id>/input.json`
- 定向模式不再静默回退到广泛采集结果
- 当前仍只支持 `ggzy.gov.cn`，不下载附件，不进入写标书主链路

## 三、当前目录结构

```text
backend/
  main.py
  api/
    router.py
  core/
    config.py
    database.py
    exceptions.py
    logger.py
    response.py
  modules/
    agent/
    discovery/
    files/
    knowledge/
    tender/

frontend/
  app/
  components/
  lib/
  types/

storage/
  discovery/
  knowledge/
  tender/
    agent_runs/
```

## 四、核心数据流

### 1. 招标主链路

```text
用户上传招标文件
  -> backend/tender.upload
  -> files.save
  -> tender.parse
  -> files.parse
  -> tender.extract
  -> 写入/复用 extract 步骤产物
  -> extract_agent
  -> OpenClaw Gateway Client
  -> Local OpenClaw Gateway
  -> tender.judge
  -> 写入/复用 judge 步骤产物
  -> orchestrator 检索知识
  -> judge_agent
  -> OpenClaw Gateway Client
  -> Local OpenClaw Gateway
  -> tender.generate
  -> 写入/复用 generate 步骤产物
  -> orchestrator 检索知识
  -> generate_agent
  -> OpenClaw Gateway Client
  -> Local OpenClaw Gateway
  -> 返回前端展示
```

### 2. 知识库链路

```text
用户上传知识文档
  -> frontend /knowledge 发起 upload/process/retrieve/content/download/delete
  -> knowledge.upload
  -> 本地保存原始文件
  -> knowledge.process
  -> 文本解析
  -> 规则切块
  -> 写入 knowledge_documents / knowledge_chunks
  -> knowledge.retrieve
  -> knowledge.content / knowledge.download / knowledge.delete
  -> orchestrator 消费结果
```

### 3. 项目发现链路

```text
用户进入 /discovery
  -> frontend 请求 /api/discovery/profile
  -> discovery.service 聚合 processed knowledge documents
  -> 生成企业能力画像与推荐采集方向

用户点击“按推荐方向采集”
  -> frontend POST /api/discovery/runs
  -> discovery.service 归一化 targeting payload
  -> agent.collect_agent
  -> OpenClaw Gateway Client
  -> Local OpenClaw Gateway
  -> collect_ggzy.py
  -> ggzy collector
  -> 写入 project_discovery_runs / project_leads
  -> frontend 拉取 /api/discovery/projects / {lead_id}
```

## 五、Agent 与知识库的关系

当前约束：

- Agent 不直接访问数据库
- Agent 不直接调用 repository
- 统一由 backend orchestrator 调用 `KnowledgeService.retrieve`

当前知识来源映射：

- `judge` -> `qualifications + project_cases`
- `generate` -> `company_profile + templates + project_cases`

orchestrator 负责：

1. 根据任务类型选择知识来源
2. 为每类来源生成检索 query
3. 合并检索结果并去重
4. 格式化为 `context_text`
5. 把上下文传给 Agent

## 六、数据存储

### 1. MySQL

当前 MySQL 主要用于知识库和项目发现：

- `knowledge_documents`
- `knowledge_chunks`
- `project_discovery_runs`
- `project_leads`

### 2. Local Storage

当前本地文件存储主要用于：

- 招标文件原始文件
- 招标解析文本
- 招标 Agent 步骤产物
- 知识文档原始文件
- 知识文档解析文本
- discovery 采集输入输出与线索详情快照
- 招标本地 JSON 记录

当前招标步骤产物目录：

- `storage/tender/agent_runs/<file_id>/extract/`
- `storage/tender/agent_runs/<file_id>/judge/`
- `storage/tender/agent_runs/<file_id>/generate/`

当前 discovery 产物目录：

- `storage/discovery/agent_runs/<run_id>/input.json`
- `storage/discovery/agent_runs/<run_id>/status.json`
- `storage/discovery/agent_runs/<run_id>/output.json`
- `storage/discovery/leads/<lead_id>/detail.txt`
- `storage/discovery/leads/<lead_id>/raw_snapshot.json`

每个步骤固定输出：

- `input.json`
- `status.json`
- `output.json`

当前恢复规则：

- 若 `status.json.state == success` 且 `output.json` 完整，则直接复用
- 若 `state == running` 且存在 `run_id`，则优先继续 `agent.wait`
- 若 `state == error` 或产物不完整，则覆盖步骤目录后重跑

当前本机联调状态：

- `health` 已通过 Gateway 客户端真实验证
- `collect / extract / judge / generate` 已走本地 OpenClaw Gateway
- `extract / judge / generate` 已完成服务层真实联调
- Gateway 若启用 token 鉴权，则后端需显式提供 `OPENCLAW_GATEWAY_TOKEN`

## 七、当前扩展点

已预留但未完成：

- PDF 解析
- 招标主链路 MySQL 化
- 异步 worker
- 更复杂的 discovery 方向词生成、检索和重排
- Gateway HTTP 接口级联调与稳定性验证

## 八、当前架构边界

当前不做：

- 微服务拆分
- 多 Agent 扩张
- 向量数据库
- 复杂权限体系
- 审批流

原则是：简单优先、可运行优先、小步迭代。

# Discovery 模块说明

## 目标

discovery 模块是写标书主链路前的一层人工筛选入口，用于：

- 手动发现公开项目。
- 形成内部线索池。
- 基于现有知识库给出推荐分、推荐理由和风险提示。
- 由用户人工判断是否继续进入正式招标处理。

当前阶段不做：

- 多站聚合。
- 附件下载。
- 附件解析。
- 自动进入写标书流程。

## 当前范围

### 数据源

- 当前只支持 `ggzy.gov.cn`。
- 只保留发起类公告：
  - `招标公告`
  - `采购公告`
  - `公开招标公告`
- 排除结果类、澄清类、终止类和变更类公告。

### Agent 约束

- 使用 `collect_agent` 负责 discovery 前置采集。
- `collect_agent` 不下载附件。
- `collect_agent` 不进入写标书主链路。
- `collect_agent` 的 OpenClaw agent id 为 `tender-collect`。

## 后端结构

### 模块目录

- `backend/modules/discovery/router.py`
- `backend/modules/discovery/service.py`
- `backend/modules/discovery/repository.py`
- `backend/modules/discovery/schema.py`
- `backend/modules/discovery/model.py`
- `backend/modules/discovery/artifacts.py`

### 数据表

#### `project_discovery_runs`

用于记录每次手动采集执行。

关键字段：
- `run_id`
- `source`
- `trigger_type`
- `status`
- `started_at`
- `finished_at`
- `total_found`
- `total_new`
- `total_updated`
- `error_message`

#### `project_leads`

用于存储 discovery 线索池。

关键字段：
- `lead_id`
- `source`
- `source_notice_id`
- `title`
- `notice_type`
- `region`
- `published_at`
- `detail_url`
- `canonical_url`
- `project_code`
- `tender_unit`
- `budget_text`
- `deadline_text`
- `detail_text_path`
- `raw_snapshot_path`
- `extract_result_json`
- `match_result_json`
- `recommendation_score`
- `recommendation_level`
- `status`

## 接口

### `GET /api/discovery/status`

- 查看模块状态和采集模式。

### `POST /api/discovery/runs`

- 手动触发一次 discovery 采集。
- 当前支持三种采集模式：
  - `broad`：广泛采集
  - `targeted`：按企业画像推荐方向采集
  - `keyword`：按用户输入关键词采集

关键词采集的最小输入为：

- `keywords`：必填，最多 5 个
- `regions`：可选
- `notice_types`：可选
- `exclude_keywords`：可选

### `GET /api/discovery/runs`

- 查看最近采集记录。
- run 摘要中的 `targeting.mode` 可能为 `broad / targeted / keyword`。
- 关键词采集会把原始关键词、地区、公告类型和排除词快照写入 run targeting，便于回看和复用。

### `GET /api/discovery/projects`

- 查看线索池列表。
- 支持关键字、地区、公告类型、推荐等级和是否仅看推荐项目筛选。
- 关键词采集结果会继续进入同一线索池，不新增独立路由。

### `GET /api/discovery/projects/{lead_id}`

- 查看单个线索详情、抽取字段、推荐结果和详情正文。

## 采集链路

```text
前端 /discovery
  -> POST /api/discovery/runs
  -> DiscoveryService.run_collection
  -> AgentService.run_collect
  -> collect_agent
  -> OpenClaw tender-collect
  -> python scripts/collect_ggzy.py
  -> GgzyCollector
  -> 结构化 projects
  -> 规则抽取 + 知识库推荐评分
  -> project_leads + storage/discovery/*
  -> 前端列表 / 详情页展示
```

### 三种采集模式说明

- `broad`
  - 不依赖企业画像。
  - 直接按 `ggzy` 默认规则抓取并入库。
- `targeted`
  - 依赖企业画像推荐方向。
  - 透传关键词、地区、资质词、行业词给 `collect_agent`。
- `keyword`
  - 不依赖企业画像。
  - 直接透传用户填写的 `keywords / regions / notice_types / exclude_keywords`。
  - 若未填写关键词，接口直接报错，不回退为广泛采集。

### 关键词采集的匹配与展示

- 标题、正文、抽取关键词、地区、公告类型会参与关键词匹配评分。
- 命中 `exclude_keywords` 时会降权，并追加风险提示。
- 列表项会返回 `matched_keywords`，用于前端展示本条线索命中了哪些输入关键词。
- 当关键词采集结果为 0 时，前端不只显示空列表，还会提示可放宽地区、减少关键词、删除排除词，或切换到广泛采集。

## 120 秒内返回的控制策略

OpenClaw Gateway 当前超时窗口为 `120s`。为了尽量稳定在这一窗口内返回，这一版做了以下限制：

- `DISCOVERY_GGZY_MAX_PROJECTS=5`
- `DISCOVERY_GGZY_TIMEOUT_SECONDS=8`
- `DISCOVERY_GGZY_BUDGET_SECONDS=95`
- `DISCOVERY_GGZY_DETAIL_TEXT_LIMIT=2000`

设计原则：

- 用约 `95s` 做实际页面抓取。
- 给 OpenClaw run 收尾保留余量。
- 只返回预算内抓取完成的项目，不等待慢页面。
- `detail_text` 只保留必要正文，避免会话结果过大。

### 完整项目判定

当前 discovery 只把满足基本字段的项目计入结果：

- `title`
- `notice_type`
- `published_at`
- `detail_url`
- `canonical_url`
- `detail_text`

如果不满足，项目不会进入线索池。

## 超时处理

已修复一种实际发生过的情况：

- OpenClaw 页面里已经出现 assistant 返回。
- 但 `agent.wait` 在 `120s` 内仍返回 `timeout`。

当前处理方式：

- `agent.wait` 超时后，后端会再检查 session。
- 如果 session 中已经有有效结果，则直接回收并继续后续入库。
- 只有在 session 里也拿不到有效结果时，才真正视为失败或回退。

## OpenClaw 连接补充

- Gateway 握手成功后会持久化新的 `deviceToken`。
- 若本地缓存 token 与网关状态不匹配，会自动清理 `OPENCLAW_STATE_DIR/identity/device-auth.json` 后重试 1 次。
- 该修复主要用于降低本地首次接入或网关重置后的连接失败概率。

## 产物落地

### run 级产物

- `storage/discovery/agent_runs/<run_id>/input.json`
- `storage/discovery/agent_runs/<run_id>/status.json`
- `storage/discovery/agent_runs/<run_id>/output.json`

### lead 级产物

- `storage/discovery/leads/<lead_id>/detail.txt`
- `storage/discovery/leads/<lead_id>/raw_snapshot.json`

## 前端页面

- `/discovery`
  - 手动触发采集。
  - 查看线索池。
  - 查看最近采集摘要。
- `/discovery/[leadId]`
  - 查看正文。
  - 查看抽取字段。
  - 查看推荐理由、风险和命中知识。

## 当前未完成

- 多站采集。
- 附件级处理。
- 浏览器级 E2E 自动化。
- discovery 到主链路的半自动推进。
- 关键词采集第一版仍不做自动补全、常用策略保存和复杂同义词扩展。

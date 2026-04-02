# API 设计说明

本文档描述当前已经实现并可直接联调的接口。

## 统一返回结构

### 成功

```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```

### 失败

```json
{
  "success": false,
  "message": "可读错误信息",
  "data": {}
}
```

约束：
- 所有接口均返回 JSON。
- 所有失败场景都必须提供可读 `message`。
- 前端统一按 `loading / success / error` 展示状态。

## 健康检查

### GET /api/health

用途：
- 检查后端服务是否可用。

返回示例：

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "status": "ok"
  }
}
```

## 项目发现模块

当前只支持 `ggzy` 单站手动采集。

### GET /api/discovery/status

用途：
- 查看 discovery 模块状态。
- 查看当前采集模式是否为 `openclaw-agent` 或 `disabled`。

返回示例：

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "module": "discovery",
    "status": "ready",
    "message": "discovery module is ready for manual project collection",
    "mock": false,
    "collect_mode": "openclaw-agent",
    "available_routes": [
      "/api/discovery/status",
      "/api/discovery/runs",
      "/api/discovery/projects",
      "/api/discovery/projects/{lead_id}"
    ],
    "supported_sources": [
      "ggzy"
    ],
    "repository_ready": true
  }
}
```

### POST /api/discovery/runs

用途：
- 触发一次手动项目采集。

请求体：

```json
{
  "source": "ggzy"
}
```

返回示例：

```json
{
  "success": true,
  "message": "项目采集执行成功。",
  "data": {
    "run_id": "c6309701f5d141eb8a30e3286e3af658",
    "source": "ggzy",
    "trigger_type": "manual",
    "status": "success",
    "started_at": "2026-04-01 08:48:22",
    "finished_at": "2026-04-01 08:49:56",
    "total_found": 2,
    "total_new": 0,
    "total_updated": 2,
    "error_message": ""
  }
}
```

### GET /api/discovery/runs

用途：
- 查看最近采集记录。

返回示例：

```json
{
  "success": true,
  "message": "项目采集记录获取成功。",
  "data": {
    "items": [
      {
        "run_id": "c6309701f5d141eb8a30e3286e3af658",
        "source": "ggzy",
        "trigger_type": "manual",
        "status": "success",
        "started_at": "2026-04-01 08:48:22",
        "finished_at": "2026-04-01 08:49:56",
        "total_found": 2,
        "total_new": 0,
        "total_updated": 2,
        "error_message": ""
      }
    ]
  }
}
```

### GET /api/discovery/projects

用途：
- 查看 discovery 线索池。
- 支持关键字、地区、公告类型、推荐等级和是否仅看推荐项目筛选。

查询参数：
- `keyword`
- `region`
- `notice_type`
- `recommendation_level`
- `recommended_only`
- `page`
- `page_size`

返回示例：

```json
{
  "success": true,
  "message": "项目线索列表获取成功。",
  "data": {
    "items": [
      {
        "lead_id": "0afb50dc314b40d28cf7e3d2be960e9f",
        "source": "ggzy",
        "title": "某项目公开招标公告",
        "notice_type": "公开招标公告",
        "region": "甘肃",
        "published_at": "2026-04-01 00:00:00",
        "project_code": "ABC20260401",
        "tender_unit": "某采购单位",
        "budget_text": "500万元",
        "deadline_text": "2026-04-08 09:00:00",
        "recommendation_score": 70,
        "recommendation_level": "medium",
        "recommendation_reasons": [
          "命中企业资质材料，可支撑资格匹配说明。"
        ]
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
  }
}
```

### GET /api/discovery/projects/{lead_id}

用途：
- 查看单个项目详情、抽取结果、推荐结果和详情正文。

返回示例：

```json
{
  "success": true,
  "message": "项目线索详情获取成功。",
  "data": {
    "lead_id": "0afb50dc314b40d28cf7e3d2be960e9f",
    "source": "ggzy",
    "title": "某项目公开招标公告",
    "notice_type": "公开招标公告",
    "region": "甘肃",
    "published_at": "2026-04-01 00:00:00",
    "detail_url": "https://www.ggzy.gov.cn/...",
    "canonical_url": "https://www.ggzy.gov.cn/...",
    "extract_result": {
      "project_name": "某项目",
      "tender_unit": "某采购单位",
      "project_code": "ABC20260401",
      "region": "甘肃",
      "budget_text": "500万元",
      "deadline_text": "2026-04-08 09:00:00",
      "notice_type": "公开招标公告",
      "published_at": "2026-04-01 00:00:00",
      "qualification_requirements": [
        "具备相关资质"
      ],
      "keywords": [
        "智慧园区"
      ]
    },
    "match_result": {
      "recommendation_score": 70,
      "recommendation_level": "medium",
      "recommendation_reasons": [
        "命中企业资质材料，可支撑资格匹配说明。"
      ],
      "risks": [
        "预算信息缺失，需要补充商务评估。"
      ],
      "matched_knowledge": [
        {
          "category": "qualifications",
          "document_title": "资质证书汇编",
          "section_title": "软件企业证书"
        }
      ]
    },
    "detail_text": "..."
  }
}
```

## 招标处理主链路

### POST /api/tender/upload

用途：
- 上传招标文件。

请求类型：
- `multipart/form-data`

请求字段：
- `file`
- `source_type`
- `source_url`

说明：
- 当前优先支持 `txt / docx`。
- `pdf` 上传入口保留，但真实解析仍未补齐。

### POST /api/tender/parse

用途：
- 解析招标文件文本。

### POST /api/tender/extract

用途：
- 抽取核心字段。

### POST /api/tender/judge

用途：
- 输出投标建议。

### POST /api/tender/generate

用途：
- 生成标书初稿。

说明：
- `extract / judge / generate` 对外响应结构保持稳定。
- 当前招标主链路强制经由本地 OpenClaw Gateway 调用。
- OpenClaw 不可用、返回空结果或返回非法 JSON 时，接口直接返回可读错误。

## OpenClaw 与产物

### 关键环境变量

- `OPENCLAW_GATEWAY_URL`
- `OPENCLAW_GATEWAY_TOKEN`
- `OPENCLAW_GATEWAY_PASSWORD`
- `OPENCLAW_AGENT_COLLECT`
- `OPENCLAW_AGENT_EXTRACT`
- `OPENCLAW_AGENT_JUDGE`
- `OPENCLAW_AGENT_GENERATE`

### discovery 相关环境变量

- `DISCOVERY_SOURCE_ENABLED_GGZY`
- `DISCOVERY_COLLECT_USE_OPENCLAW_AGENT`
- `DISCOVERY_COLLECT_USE_REAL_GGZY`
- `DISCOVERY_GGZY_LIST_URL`
- `DISCOVERY_GGZY_MAX_PROJECTS`
- `DISCOVERY_GGZY_TIMEOUT_SECONDS`
- `DISCOVERY_GGZY_BUDGET_SECONDS`
- `DISCOVERY_GGZY_DETAIL_TEXT_LIMIT`

### discovery 产物路径

- `storage/discovery/agent_runs/<run_id>/input.json`
- `storage/discovery/agent_runs/<run_id>/status.json`
- `storage/discovery/agent_runs/<run_id>/output.json`
- `storage/discovery/leads/<lead_id>/detail.txt`
- `storage/discovery/leads/<lead_id>/raw_snapshot.json`

### discovery 当前约束

- 只采集 `ggzy.gov.cn`。
- 不下载附件，不进入写标书主链路。
- 默认预算控制为 `95s`，默认最大候选项目数为 `5`，默认单请求超时为 `8s`。
- 只返回预算内抓取完成的项目。
- `detail_text` 默认截断到 `2000` 字。
- 当 `agent.wait` 超时但 session 已有结果时，后端会回收 session 中的已生成结果，避免误判失败。

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

当前只支持 `ggzy` 单站项目发现，但已支持三种模式：

- `broad`：广泛采集
- `targeted`：基于企业能力画像的定向采集
- `keyword`：基于用户输入关键词的主动采集

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
      "/api/discovery/profile",
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

### GET /api/discovery/profile

用途：
- 返回当前企业能力画像。
- 返回基于知识库生成的推荐采集方向。
- 在知识库资料不足时，返回可读提示但不阻塞 discovery 页面。

返回示例：

```json
{
  "success": true,
  "message": "企业能力画像获取成功。",
  "data": {
    "has_profile": true,
    "message": "已根据 5 份已处理资料生成 3 个推荐采集方向。",
    "document_counts": {
      "company_profile": 2,
      "qualifications": 1,
      "project_cases": 1,
      "templates": 1
    },
    "directions": [
      {
        "profile_key": "qualification-track",
        "title": "资质能力导向项目",
        "description": "优先追踪与现有资质和资格条件更匹配的项目。",
        "confidence": "medium",
        "keywords": ["污水处理", "环保工程"],
        "regions": ["陕西"],
        "qualification_terms": ["ISO9001", "环保工程专业承包"],
        "industry_terms": ["污水处理"],
        "reasons": [
          "已处理 1 份资质资料，可反推适合追踪的资格条件。"
        ],
        "supporting_documents": [
          {
            "category": "qualifications",
            "document_title": "资质证书",
            "section_title": "二、资质证书"
          }
        ],
        "gap_message": "缺少项目案例支撑，当前更适合做资格匹配初筛。"
      }
    ]
  }
}
```

### POST /api/discovery/runs

用途：
- 触发一次手动项目采集。
- 支持广泛采集、定向采集和关键词采集。
- 定向/关键词采集参数会作为采集意图透传给真实 OpenClaw `collect_agent`。

请求体：

```json
{
  "source": "ggzy",
  "mode": "keyword",
  "profile_key": "",
  "profile_title": "",
  "keywords": ["智慧园区", "弱电集成"],
  "regions": ["甘肃"],
  "notice_types": ["招标公告"],
  "exclude_keywords": ["监理"],
  "qualification_terms": [],
  "industry_terms": []
}
```

说明：
- 若 `mode=broad`，其余 targeting 字段可为空。
- 若 `mode=targeted` 但未提供有效 targeting 词，后端会自动回退为 `broad`。
- 若 `mode=keyword` 且 `keywords` 为空，接口直接返回错误。
- `notice_types` 和 `exclude_keywords` 当前只作为 discovery 采集与推荐评分条件，不改变既有路由语义。
- 定向模式不再静默回退到广泛采集结果；未命中当前方向时接口会直接返回错误。

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
    "error_message": "",
    "targeting": {
      "mode": "keyword",
      "profile_key": "",
      "profile_title": "",
      "keywords": ["智慧园区", "弱电集成"],
      "regions": ["甘肃"],
      "notice_types": ["招标公告"],
      "exclude_keywords": ["监理"],
      "qualification_terms": [],
      "industry_terms": []
    }
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
        "error_message": "",
        "targeting": {
          "mode": "keyword",
          "profile_key": "",
          "profile_title": "",
          "keywords": ["智慧园区", "弱电集成"],
          "regions": ["甘肃"],
          "notice_types": ["招标公告"],
          "exclude_keywords": ["监理"],
          "qualification_terms": [],
          "industry_terms": []
        }
      }
    ]
  }
}
```

### GET /api/discovery/projects

用途：
- 查看 discovery 线索池。
- 支持关键字、地区、公告类型、推荐等级、方向和是否仅看推荐项目筛选。
- 默认按 `targeting_match_score -> recommendation_score -> published_at` 排序。

查询参数：
- `keyword`
- `region`
- `notice_type`
- `recommendation_level`
- `profile_key`
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
        "targeting_match_score": 52,
        "profile_key": "",
        "profile_title": "关键词采集",
        "matched_keywords": ["智慧园区"],
        "recommendation_reasons": [
          "命中关键词：智慧园区",
          "命中公告类型：招标公告"
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
      "knowledge_support_score": 65,
      "targeting_match_score": 52,
      "profile_key": "qualification-track",
      "profile_title": "资质能力导向项目",
      "recommendation_reasons": [
        "命中企业资质材料，可支撑资格匹配说明。"
      ],
      "targeting_reasons": [
        "命中关键词：污水处理",
        "命中地区：甘肃"
      ],
      "risks": [
        "预算信息缺失，需要补充商务评估。"
      ],
      "knowledge_gaps": [
        "缺少可复用的同类项目案例"
      ],
      "matched_keywords": [
        "污水处理"
      ],
      "matched_regions": [
        "甘肃"
      ],
      "matched_qualification_terms": [
        "ISO9001"
      ],
      "matched_industry_terms": [
        "环保工程"
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

补充说明：
- `matched_keywords` 用于前端在列表中展示当前线索命中了哪些关键词输入。
- `profile_title` 在 `mode=keyword` 时固定展示为 `关键词采集`，不依赖企业画像。

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

- `OPENCLAW_TIMEOUT_SECONDS`
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
- OpenClaw Gateway 的默认等待超时为 `240s`。
- 只返回预算内抓取完成的项目。
- `detail_text` 默认截断到 `2000` 字。
- 当 `agent.wait` 超时但 session 已有结果时，后端会回收 session 中的已生成结果，避免误判失败。
- 定向采集参数会写入数据库快照和 `storage/discovery/agent_runs/<run_id>/input.json`，便于排查。

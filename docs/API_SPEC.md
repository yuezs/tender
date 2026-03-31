# API 设计说明

本文档只描述当前代码已实现的接口。

## 一、统一返回结构

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

说明：

- 所有接口返回 JSON
- 所有错误必须有可读 `message`
- 前端基于统一结构展示 `loading / success / error`

## 二、健康检查

### GET /api/health

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

## 三、招标模块

### 1. GET /api/tender/status

用途：

- 查看招标模块状态

### 2. POST /api/tender/upload

用途：

- 上传招标文件

请求类型：

- `multipart/form-data`

请求字段：

- `file`: 必填
- `source_type`: 可选，默认 `upload`
- `source_url`: 可选，当前仅预留

说明：

- 当前优先支持 `txt / docx`
- `pdf` 可上传，但解析阶段尚未真正支持

返回示例：

```json
{
  "success": true,
  "message": "招标文件上传成功",
  "data": {
    "file_id": "4d1e1f0d8b434b17a1d2f2f1e93b65d4",
    "file_name": "sample.txt",
    "source_type": "upload",
    "extension": "txt"
  }
}
```

### 3. POST /api/tender/parse

用途：

- 解析招标文件文本

请求体：

```json
{
  "file_id": "4d1e1f0d8b434b17a1d2f2f1e93b65d4"
}
```

返回示例：

```json
{
  "success": true,
  "message": "招标文件解析成功",
  "data": {
    "file_id": "4d1e1f0d8b434b17a1d2f2f1e93b65d4",
    "text": "项目名称：智慧园区平台建设项目"
  }
}
```

### 4. POST /api/tender/extract

用途：

- 抽取核心字段

请求体：

```json
{
  "file_id": "4d1e1f0d8b434b17a1d2f2f1e93b65d4"
}
```

返回示例：

```json
{
  "success": true,
  "message": "核心字段抽取成功",
  "data": {
    "project_name": "智慧园区平台建设项目",
    "tender_company": "某市大数据局",
    "budget": "500万元",
    "deadline": "2026-04-15 09:00",
    "qualification_requirements": [
      "具备软件企业资质证书"
    ],
    "delivery_requirements": [
      "合同签订后90日内完成上线"
    ],
    "scoring_focus": [
      "技术方案",
      "项目团队",
      "类似案例"
    ]
  }
}
```

说明：

- 当前为规则提取 + mock 兜底

### 5. POST /api/tender/judge

用途：

- 输出投标建议

请求体：

```json
{
  "file_id": "4d1e1f0d8b434b17a1d2f2f1e93b65d4"
}
```

返回示例：

```json
{
  "success": true,
  "message": "投标建议生成成功",
  "data": {
    "should_bid": true,
    "reason": "项目要求与公司能力较匹配，建议继续推进。",
    "risks": [
      "交付周期较紧"
    ],
    "knowledge_used": [
      {
        "category": "qualifications",
        "document_title": "资质证书汇编",
        "section_title": "软件企业证书"
      }
    ],
    "prompt_preview": "..."
  }
}
```

说明：

- `judge_agent` 不直接访问数据库
- 由 orchestrator 先检索 `qualifications + project_cases`
- 当前输出仍是 mock / 规则版，但知识检索链路是真实的

### 6. POST /api/tender/generate

用途：

- 生成标书初稿

请求体：

```json
{
  "file_id": "4d1e1f0d8b434b17a1d2f2f1e93b65d4"
}
```

返回示例：

```json
{
  "success": true,
  "message": "标书初稿生成成功",
  "data": {
    "company_intro": "...",
    "project_cases": "...",
    "implementation_plan": "...",
    "business_response": "...",
    "knowledge_used": [
      {
        "category": "company_profile",
        "document_title": "公司介绍2026版",
        "section_title": "核心能力"
      }
    ],
    "prompt_preview": "..."
  }
}
```

说明：

- `generate_agent` 不直接访问数据库
- 由 orchestrator 先检索 `company_profile + templates + project_cases`
- 当前输出仍是 mock / 规则版

## 四、知识库模块

### 1. GET /api/knowledge/status

用途：

- 查看知识库模块状态

### 2. POST /api/knowledge/documents/upload

用途：

- 上传知识文档

请求类型：

- `multipart/form-data`

请求字段：

- `file`: 必填
- `title`: 必填
- `category`: 必填
- `tags`: 可选，逗号分隔字符串
- `industry`: 可选，逗号分隔字符串

返回示例：

```json
{
  "success": true,
  "message": "知识文档上传成功",
  "data": {
    "document_id": "1db0e7717ad44b35a8c3187dcaf3b8ee",
    "title": "公司介绍2026版",
    "category": "company_profile"
  }
}
```

### 3. GET /api/knowledge/documents

用途：

- 获取知识文档列表

查询参数：

- `category`: 可选
- `status`: 可选

返回示例：

```json
{
  "success": true,
  "message": "知识文档列表获取成功",
  "data": {
    "items": [
      {
        "document_id": "1db0e7717ad44b35a8c3187dcaf3b8ee",
        "title": "公司介绍2026版",
        "category": "company_profile",
        "file_name": "company_profile.txt",
        "tags": ["公司", "能力", "案例"],
        "industry": ["政务"],
        "status": "processed",
        "chunk_count": 5,
        "created_at": "2026-03-31T03:00:00",
        "updated_at": "2026-03-31T03:01:00"
      }
    ]
  }
}
```

### 4. POST /api/knowledge/documents/{document_id}/process

用途：

- 解析文档并切块入库

返回示例：

```json
{
  "success": true,
  "message": "知识文档处理成功",
  "data": {
    "document_id": "1db0e7717ad44b35a8c3187dcaf3b8ee",
    "chunk_count": 5,
    "status": "processed"
  }
}
```

### 5. POST /api/knowledge/retrieve

用途：

- 检索知识片段

请求体：

```json
{
  "category": "project_cases",
  "query": "智慧园区",
  "tags": ["案例"],
  "industry": ["政务"],
  "limit": 5
}
```

返回示例：

```json
{
  "success": true,
  "message": "知识检索成功",
  "data": {
    "chunks": [
      {
        "id": "c47e0b87dd4d47f0b01d15709a0ef4af",
        "document_id": "1db0e7717ad44b35a8c3187dcaf3b8ee",
        "document_title": "案例库",
        "section_title": "智慧园区项目案例",
        "content": "..."
      }
    ]
  }
}
```

说明：

- 当前检索方式为：
  - 分类过滤
  - tags 过滤
  - industry 过滤
  - `LIKE` 关键词匹配
- 当前不做向量检索

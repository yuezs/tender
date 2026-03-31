# 简易知识库设计说明

## 一、目标

为 AI 招投标助手提供一套轻量可运行的企业知识库能力，服务于 `judge_agent` 和 `generate_agent`。

当前阶段要求：

- 使用 MySQL
- 不使用 PostgreSQL
- 不使用 JSONB
- 不使用复杂向量检索
- 不做复杂权限

## 二、支持的资料类型

当前只支持以下 4 类：

1. `company_profile`
2. `qualifications`
3. `project_cases`
4. `templates`

## 三、当前已实现能力

### 1. 文档上传

- 支持知识文档上传
- 原文件保存到本地 `storage/knowledge/raw/`

### 2. 文档列表

- 支持查看文档列表
- 支持按 `category` 和 `status` 过滤

### 3. 文档处理

- 支持解析文本
- 支持规则切块
- 处理后写入 MySQL

### 4. 简单检索

当前检索规则为：

- 分类过滤
- tags 过滤
- industry 过滤
- `LIKE` 关键词匹配

当前不做：

- 向量检索
- rerank
- 复杂排序策略

## 四、当前数据表

### 1. knowledge_documents

用于保存文档元数据。

关键字段：

- `document_id`
- `title`
- `category`
- `file_name`
- `extension`
- `tags`
- `industry`
- `storage_path`
- `parsed_text_path`
- `status`
- `error_message`
- `chunk_count`
- `content_length`
- `created_at`
- `updated_at`

### 2. knowledge_chunks

用于保存切块结果。

关键字段：

- `chunk_id`
- `document_id`
- `category`
- `document_title`
- `tags`
- `industry`
- `section_title`
- `content`
- `chunk_index`
- `created_at`

## 五、当前文件存储结构

```text
storage/knowledge/
  raw/
    company_profile/
    qualifications/
    project_cases/
    templates/
  parsed/
  chunks/
```

## 六、当前处理流程

```text
上传知识文档
  -> 保存原文件
  -> 写 knowledge_documents
  -> 处理文档
  -> 解析文本
  -> 规则切块
  -> 写 knowledge_chunks
  -> 提供 retrieve 能力
```

## 七、与 Agent 的集成方式

当前约束：

- Agent 不直接访问数据库
- 统一由 backend orchestrator 调用知识检索

### 1. judge_agent

知识来源：

- `qualifications`
- `project_cases`

### 2. generate_agent

知识来源：

- `company_profile`
- `templates`
- `project_cases`

### 3. orchestrator 职责

- 根据任务类型选择知识来源
- 调用 `KnowledgeService.retrieve`
- 合并和去重知识片段
- 格式化 `context_text`
- 将上下文传给 Agent

## 八、当前支持的文件类型

当前优先支持：

- `txt`
- `docx`

当前未完成：

- `pdf`

## 九、当前边界

- 不做向量数据库
- 不做复杂权限
- 不做审批流
- 不做自动同步网盘
- 不做复杂 RAG

## 十、后续演进方向

1. 增加知识库前端管理页
2. 增加文档详情与片段预览
3. 增加更细粒度检索策略
4. 在需要时再评估向量检索

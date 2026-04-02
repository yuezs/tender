---
name: tender-orchestrator
description: 招投标工作流编排器，管理整个处理流程和知识检索
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins: []
      env: []
    emoji: "🎯"
    homepage: https://github.com/zhihuigu/tender
---

# 工作流编排

协调整个招标处理工作流，管理 Agent 调用和知识检索。

## 功能

- 工作流执行管理
- Agent 任务调度
- 知识库检索路由
- 错误处理与恢复
- 状态持久化

## 工作流步骤

| 步骤 | Agent | 输入 | 输出 |
|------|-------|------|------|
| 1. 上传 | - | 招标文件 | file_id |
| 2. 解析 | files | file_id | 文本内容 |
| 3. 抽取 | extract_agent | 文本 | 结构化字段 |
| 4. 知识检索(J) | orchestrator | 字段 | 知识上下文(J) |
| 5. 判断 | judge_agent | 字段+知识 | 判断结果 |
| 6. 知识检索(G) | orchestrator | 字段+判断 | 知识上下文(G) |
| 7. 生成 | generate_agent | 字段+判断+知识 | 标书初稿 |

## 知识检索

### judge_agent 知识来源

```json
{
  "qualifications": [...],
  "project_cases": [...]
}
```

### generate_agent 知识来源

```json
{
  "company_profile": "...",
  "templates": [...],
  "project_cases": [...]
}
```

## 状态管理

### 状态文件位置

```
storage/tender/agent_runs/<file_id>/status.json
```

### 状态结构

```json
{
  "file_id": "uuid",
  "current_step": "extract|judge|generate",
  "steps": {
    "upload": { "status": "success|error|running", "output": {} },
    "extract": { "status": "success|error|running", "output": {} },
    "judge": { "status": "success|error|running", "output": {} },
    "generate": { "status": "success|error|running", "output": {} }
  },
  "error": null,
  "started_at": "timestamp",
  "updated_at": "timestamp"
}
```

## 恢复机制

### 检查点

每个步骤完成后保存状态，包括：
- 步骤输入
- 步骤输出
- 错误信息（如果有）

### 恢复逻辑

1. 检查是否存在状态文件
2. 读取当前步骤
3. 如果步骤状态为 running，尝试继续执行
4. 如果步骤状态为 error，重新执行该步骤
5. 如果步骤状态为 success，跳过并执行下一步

## 错误处理

### 重试策略

| 错误类型 | 最大重试次数 | 间隔 |
|----------|-------------|------|
| 网络错误 | 3 | 5s |
| Agent 错误 | 2 | 10s |
| 知识检索失败 | 1 | - |

### 错误响应

```json
{
  "error": true,
  "code": "ERROR_CODE",
  "message": "错误描述",
  "step": "当前步骤",
  "retryable": true
}
```

## 依赖 Skills

- `workflow-engine` - 工作流引擎
- `task-orchestra` - 任务协调
- `autonomous-executor` - 自主执行
- `longrunning-agent` - 长时任务
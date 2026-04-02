---
name: tender-agents
description: AI 招投标助手 Agent 集合 - 字段抽取、投标判断、标书生成、工作流编排
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins: []
      env:
        - MYSQL_HOST
        - MYSQL_PORT
        - MYSQL_USER
        - MYSQL_PASSWORD
        - MYSQL_DATABASE
    emoji: "📋"
    homepage: https://github.com/zhihuigu/tender
---

# 招投标助手 Agent 集合

## Agent 清单

| Agent | 功能 | 位置 |
|-------|------|------|
| extract_agent | 招标文件字段抽取 | ./extract_agent/ |
| judge_agent | 投标可行性判断 | ./judge_agent/ |
| generate_agent | 标书初稿生成 | ./generate_agent/ |
| orchestrator | 工作流编排 | ./orchestrator/ |

## Skills 依赖

### 来自 ClawHub

| Skill | 用途 | 来源 |
|-------|------|------|
| docx | Word 文档解析 | clawhub |
| markdown-converter | 文档格式转换 | clawhub |
| json-toolkit | JSON 处理 | clawhub |
| json-repair-kit | JSON 修复 | clawhub |
| markdown-formatter | Markdown 格式化 | clawhub |
| workflow-engine | 工作流引擎 | clawhub |
| task-orchestra | 任务协调 | clawhub |
| autonomous-executor | 自主执行 | clawhub |
| longrunning-agent | 长时任务 | clawhub |

### 自定义 Skills

| Skill | 功能 |
|-------|------|
| tender-extract | 招标文件字段抽取 |
| tender-judge | 投标决策评估 |
| tender-generate | 标书初稿生成 |
| tender-orchestrator | 工作流编排 |

## 工作流

```
招标文件上传 → 解析 → 字段抽取 → 知识检索 → 投标判断 → 知识检索 → 标书生成 → 结果返回
```

## 文件结构

```
openclaw_agents/
├── extract_agent/
│   ├── IDENTITY.md
│   ├── AGENTS.md
│   ├── SKILL.md
│   └── prompts/
├── judge_agent/
│   ├── IDENTITY.md
│   ├── AGENTS.md
│   ├── SKILL.md
│   └── prompts/
├── generate_agent/
│   ├── IDENTITY.md
│   ├── AGENTS.md
│   ├── SKILL.md
│   └── prompts/
├── orchestrator/
│   ├── IDENTITY.md
│   ├── AGENTS.md
│   ├── SKILL.md
│   └── workflows/
├── shared/
│   ├── SOUL.md
│   ├── USER.md
│   └── TOOLS.md
└── SKILLS.md
```

## 安装依赖

```bash
# 安装 ClawHub skills
clawhub install docx
clawhub install json-toolkit
clawhub install markdown-formatter
clawhub install workflow-engine
```

## 版本历史

- 1.0.0 - 初始版本
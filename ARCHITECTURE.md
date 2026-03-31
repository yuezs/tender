# 技术架构设计

## 一、整体架构

[Frontend]
    ↓
[Backend API]
    ↓
 ┌───────────────┬───────────────┬───────────────┐
 │               │               │               │
[Parser]      [Agent]        [Knowledge]      [DB: MySQL]
                                 │
                              [File Storage]

---

## 二、模块职责

### 1. frontend
职责：
- 展示页面
- 上传文件
- 展示解析结果
- 展示投标建议
- 展示标书初稿
- 管理知识文档上传与检索

### 2. backend
职责：
- 提供统一 API 入口
- 负责任务编排
- 调用 parser / agent / knowledge
- 负责数据入库
- 负责错误处理与状态返回

建议分层：
- api/
- services/
- schemas/
- repositories/
- models/
- core/

### 3. parser
职责：
- 解析 PDF / DOCX / TXT / HTML
- 输出纯文本
- 输出基础结构化信息（可选）

### 4. agent
职责：
- 根据输入调用不同 Agent
- 组织 Prompt
- 调用 OpenClaw / LLM
- 输出结构化结果

当前只保留 4 个 Agent：
1. extract_agent
2. judge_agent
3. generate_agent
4. orchestrator

### 5. knowledge
职责：
- 保存企业知识文档
- 文档分类
- 文本解析
- 规则切块
- 简单检索
- 返回知识片段给 Agent

### 6. worker（预留）
职责：
- 处理异步任务
- 后续可处理大文件解析、OCR、批量生成

---

## 三、核心数据流

### 场景一：招标文件处理
用户上传招标文件
    ↓
backend 接收文件
    ↓
parser 解析文本
    ↓
extract_agent 抽取字段
    ↓
judge_agent 判断是否建议投标
    ↓
generate_agent 生成标书初稿
    ↓
结果返回前端并入库

### 场景二：知识库辅助生成
用户上传企业资料
    ↓
knowledge 保存文件
    ↓
knowledge 解析文本
    ↓
knowledge 切块并入库
    ↓
当 agent 需要补充企业信息时
    ↓
backend 调用 knowledge 检索
    ↓
将知识片段拼成上下文
    ↓
agent 输出更贴近企业实际的内容

---

## 四、为什么当前使用 MySQL
当前阶段重点是：
- 快速做出 MVP
- 完成结构化数据存储
- 支持简单检索和业务流程

当前不做：
- 复杂向量检索
- PostgreSQL JSONB 特性
- 高复杂度全文检索

因此当前阶段统一使用 MySQL。

---

## 五、扩展策略
当前架构是“可演进的简洁版”：

### 当前阶段
- MySQL + 简单检索
- 规则切块
- 少量 Agent
- 同步调用为主

### 后续可扩展方向
- 增加 worker 异步任务
- 增加向量检索层
- 增加知识重排
- 增加多人协作与权限
- 增加版本管理
- 增加标书导出和模板管理
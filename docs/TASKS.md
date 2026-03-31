# 开发任务状态

本文档记录当前项目任务的真实进度。

## 一、已完成

### 1. 项目骨架

- 已初始化 frontend：Next.js + TypeScript
- 已初始化 backend：FastAPI
- 已建立 backend 分层目录
- 已实现统一 JSON 返回结构
- 已实现 `/api/health`

### 2. 招标主链路 MVP

- 已实现招标文件上传接口
- 已实现文件本地保存
- 已实现 `txt / docx` 文本解析
- 已实现 `/parse`
- 已实现 `/extract`
- 已实现 `/judge`
- 已实现 `/generate`
- 已完成前后端最小联调

### 3. 简易知识库第一版

- 已创建 `knowledge_documents`
- 已创建 `knowledge_chunks`
- 已实现知识文档上传接口
- 已实现知识文档列表接口
- 已实现文档处理接口
- 已实现简单检索接口

### 4. 知识库与 Agent 链路接入

- 已实现 orchestrator 根据任务类型选择知识来源
- 已实现 `judge_agent` 使用 `qualifications + project_cases`
- 已实现 `generate_agent` 使用 `company_profile + templates + project_cases`
- 已实现知识上下文组装
- 已实现结构化结果返回

### 5. OpenClaw Gateway 接入

- 已将 Agent 调用从 CLI 子进程切换到本地 OpenClaw Gateway WebSocket RPC
- 已保持 `/api/tender/parse|extract|judge|generate` 的请求响应结构不变
- 已补充 `extract / judge / generate` 三步的 `input.json / status.json / output.json` 产物落地
- 已支持基于 `status.json + output.json` 的成功复用与最小断点续跑
- 已在 tender 本地记录中增加 `agent_artifacts` 路径信息

### 5. 前端工作台 UI 重做

- 已引入 Tailwind CSS
- 已重做左侧导航工作台布局
- 已重做首页
- 已重做招标上传页
- 已重做结果页
- 已重做知识库页面空壳
- 已验证前端 `npm run build` 通过

## 二、当前仍是 MVP / Mock

- `extract_agent` 仍保留规则提取兜底
- `judge_agent` 仍保留规则判断兜底
- `generate_agent` 仍保留模板生成兜底
- Gateway 真实联调与效果验证仍需继续补齐
- PDF 真实解析未完成
- 知识库前端真实管理功能未完成
- 招标主链路记录仍为本地 JSON，未切到 MySQL

## 三、下一阶段任务

### 1. Agent 真正接入

- 完成 Gateway `health` 与端到端联调
- 完善 Prompt 模板
- 加强输出校验、重试与兜底

### 2. 文件能力补齐

- 增加 PDF 真实解析
- 评估 OCR 是否需要纳入后续阶段

### 3. 知识库前端

- 增加知识文档上传界面
- 增加知识文档列表页
- 增加处理状态展示
- 增加检索调试页

### 4. 数据持久化收口

- 将招标主链路记录迁移到 MySQL
- 明确表结构与迁移策略

### 5. 工程质量

- 增加接口测试
- 增加关键流程回归测试
- 增加日志与错误排查指引

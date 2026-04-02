# AI 招投标助手

企业内部使用的辅助投标工作台，当前阶段为 MVP。

## 当前定位

本项目不是营销官网，也不是通用 AI 演示站。当前目标是为投标专员、商务人员、项目经理提供一条可运行的辅助链路：

1. 上传招标文件
2. 解析招标文件
3. 抽取核心字段
4. 生成投标建议
5. 生成标书初稿
6. 接入简易企业知识库

## 当前已实现

### 1. 招标主链路

- 已实现 `upload -> parse -> extract -> judge -> generate` 五步链路
- 已支持 `txt / docx` 解析
- `pdf` 当前允许上传，但解析阶段会返回明确提示，尚未实现真实解析
- 文件保存到本地 `storage/`
- 招标记录当前先保存为本地 JSON，便于 MVP 跑通

### 2. 简易知识库

- 使用 MySQL 存储 `knowledge_documents` 和 `knowledge_chunks`
- 已实现文档上传、列表、处理、简单检索
- 已实现文档全文查看、原文件下载、删除
- 前端资料中心（`/knowledge`）已支持：
  - 上传、列表、筛选、处理
  - 最近处理结果（解析摘要 / 告警 / 重点内容 / 切块预览）
  - 检索调试
  - 文档操作下拉菜单（处理 / 全文查看 / 文件下载 / 删除）
  - 检索结果三行预览 + 弹窗全文查看
- 当前只支持 4 类资料：
  - `company_profile`
  - `qualifications`
  - `project_cases`
  - `templates`
- 当前知识文档仅支持 `txt / docx`（`pdf` 未纳入知识库范围）
- 当前解析能力：
  - `txt / docx` 统一解析为结构块
  - `docx` 支持段落、标题、列表、表格顺序读取
  - 支持段内编号标题识别与长段再切分
  - `company_profile` 已增加规则版重点句提取
- 处理结果会返回：
  - `parse_summary`
  - `warnings`
  - `key_points`
  - `chunk_preview`
- 原文件与解析文本会分别落盘到：
  - `storage/knowledge/raw/`
  - `storage/knowledge/parsed/`
- 检索方式为：
  - 分类过滤
  - tags 过滤
  - industry 过滤
  - `LIKE` 关键词匹配

### 3. Agent 链路

- 当前只保留 4 个 Agent：
  - `extract_agent`
  - `judge_agent`
  - `generate_agent`
  - `orchestrator`
- Agent 不直接访问数据库
- 由 backend orchestrator 先检索知识，再组装上下文喂给 Agent
- 当前仍使用 mock / 规则版输出，但流程是真实链路

### 4. 前端工作台

- 前端使用 `Next.js + TypeScript`
- 样式层已切到 `Tailwind CSS`
- 当前页面定位为“企业内部辅助投标工作台”
- 已重做以下页面：
  - 首页
  - 招标上传页
  - 结果页
  - 知识库页面

## 技术栈

- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Backend: FastAPI + Python
- Database: MySQL
- ORM: SQLAlchemy
- File Storage: 本地 `storage/`
- Agent orchestration: OpenClaw 预留，当前用 mock/规则版链路

## 目录结构

```text
frontend/                  前端页面与组件
backend/                   后端服务
backend/core/              配置、数据库、异常、统一响应
backend/api/               API 聚合入口
backend/modules/tender/    招标主链路
backend/modules/knowledge/ 知识库模块
backend/modules/agent/     Agent 编排模块
backend/modules/files/     文件存储与解析
docs/                      项目文档
storage/                   本地文件存储
```

## 当前文档

- [PRD.md](./PRD.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [docs/API_SPEC.md](./docs/API_SPEC.md)
- [docs/KNOWLEDGE_BASE.md](./docs/KNOWLEDGE_BASE.md)
- [docs/TASKS.md](./docs/TASKS.md)

## 本地运行

### 1. MySQL

先创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS tender CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
uvicorn main:app --reload
```

后端默认读取以下环境变量：

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

默认访问：

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8000`

## 当前边界

- 未接入真实 OpenClaw / LLM
- `extract / judge / generate` 仍是 mock / 规则版
- 未实现 PDF 真实解析
- 未实现复杂权限、审批流、向量检索、RAG、rerank
- 知识库前端已实现基础管理页（上传 / 列表 / 处理 / 检索调试 / 全文查看 / 下载 / 删除），未实现编辑、向量检索、复杂排序与权限能力
- 招标链路主记录仍未切到 MySQL

## 下一步建议

1. 接入真实 OpenClaw / LLM
2. 增加知识库结构化字段提取与更稳的排序（可选）
3. 补齐 PDF 解析
4. 将招标主链路记录迁移到 MySQL
5. 增加基础自动化测试

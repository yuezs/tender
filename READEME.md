# AI 招投标助手

## 项目简介
AI 招投标助手是一个面向企业投标场景的智能辅助系统，用于帮助完成：
- 招标信息录入
- 招标文件上传与解析
- 核心字段抽取
- 是否建议投标判断
- 标书初稿生成
- 企业知识文档检索复用

本项目当前阶段为 MVP，目标是先跑通主链路，再逐步增强。

---

## MVP 范围
第一阶段只做以下能力：

1. 支持粘贴招标链接
2. 支持上传招标文件（PDF / DOCX / TXT）
3. 自动抽取项目核心字段
4. 自动判断是否建议投标
5. 自动生成标书初稿
6. 支持企业知识文档上传与简单检索
7. 支持将企业知识片段注入 Agent 上下文

---

## 目标用户
- 投标专员
- 商务人员
- 项目经理
- 售前支持人员

---

## 项目目标
通过 AI 辅助，降低人工阅读和编写标书的时间成本，提高投标效率和内容复用率。

---

## 技术栈
- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- Database: MySQL
- Agent orchestration: OpenClaw
- File parsing: Python
- Knowledge base (MVP): MySQL + 文件存储 + 规则切块 + 简单检索

---

## 当前架构模块
- frontend：前端页面
- backend：API 服务
- parser：文档解析
- agent：Agent 编排
- knowledge：简易知识库
- worker：预留异步任务能力

---

## 启动方式（开发阶段）

### backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# 开发任务拆解

## 第一阶段：项目骨架
目标：
- 初始化前后端项目
- 建立目录结构
- 建立基础 API
- 建立基础页面

任务：
1. 初始化 frontend（Next.js + TypeScript）
2. 初始化 backend（FastAPI）
3. 建立 backend 分层目录
4. 创建 health 接口
5. 创建首页 / 上传页 / 结果页

---

## 第二阶段：招标文件链路
目标：
- 实现从上传到解析的最小闭环

任务：
1. 实现招标文件上传接口
2. 保存文件到本地 storage
3. 实现 txt/docx/pdf 解析（可先支持两种）
4. 实现抽取接口（可先 mock）
5. 实现判断接口（可先 mock）
6. 实现生成接口（可先 mock）

---

## 第三阶段：Agent 接入
目标：
- 接入 OpenClaw / Agent 编排

任务：
1. 建立 extract_agent
2. 建立 judge_agent
3. 建立 generate_agent
4. 建立 orchestrator
5. 统一 Prompt 模板
6. 输出结构化 JSON

---

## 第四阶段：简易知识库
目标：
- 建立知识文档上传、处理、检索能力

任务：
1. 建表：knowledge_documents / knowledge_chunks
2. 实现文档上传接口
3. 实现文档列表接口
4. 实现解析与切块
5. 实现简单检索
6. 接入 judge_agent / generate_agent

---

## 第五阶段：联调
目标：
- 跑通主流程

任务：
1. 文件上传 -> 解析 -> 抽取
2. 抽取 -> 投标建议
3. 抽取 + 知识检索 -> 初稿生成
4. 前后端联调
5. 补充错误提示与加载状态

---

## 第六阶段：优化
目标：
- 提升可用性

任务：
1. 统一接口返回结构
2. 增加日志
3. 增加异常处理
4. 增加 mock / real 开关
5. 补充基础测试
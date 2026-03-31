# 简易知识库设计说明

## 一、目标
为 AI 招投标助手提供一个轻量级企业知识库，支持：
- 企业资料上传
- 文档分类管理
- 文本解析
- 文本切块
- 简单检索
- 为 Agent 提供企业知识上下文

---

## 二、当前支持的知识类型
仅支持以下 4 类：

1. `company_profile`
   - 公司介绍
   - 企业概况
   - 核心能力
   - 服务优势

2. `qualifications`
   - 营业执照
   - 行业资质
   - 认证证书
   - 荣誉奖项

3. `project_cases`
   - 历史中标项目
   - 类似项目案例
   - 成功实施案例

4. `templates`
   - 技术方案模板
   - 商务应答模板
   - 售后服务模板
   - 常用标书段落

---

## 三、设计原则
- 先简单可用
- 先分类再检索
- 先规则切块再考虑向量化
- 检索结果必须可追溯
- Agent 不直接查数据库，由后端统一调用

---

## 四、目录建议
知识库相关代码建议放在：
backend/modules/knowledge/
├─ router.py
├─ service.py
├─ repository.py
├─ schemas.py
├─ models.py
├─ parser.py
├─ chunker.py
└─ retriever.py
文件存储建议放在：
storage/knowledge/
├─ raw/
│  ├─ company_profile/
│  ├─ qualifications/
│  ├─ project_cases/
│  └─ templates/
├─ parsed/
└─ chunks/
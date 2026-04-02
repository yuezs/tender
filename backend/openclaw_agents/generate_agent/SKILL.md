---
name: tender-generate
description: 生成完整标书主干初稿，包含公司介绍、资质响应、案例、实施方案、服务承诺和商务响应
version: 1.1.0
metadata:
  openclaw:
    requires:
      bins: []
      env: []
    emoji: "📝"
    homepage: https://github.com/zhihuigu/tender
---

# 标书主干生成

基于招标字段、投标建议和知识库上下文，生成适合当前项目的完整标书主干 JSON。

## 输入
1. `tender_fields`
2. `judge_result`
3. `knowledge_context`
   - `company_profile`
   - `qualifications`
   - `project_cases`
   - `templates`

## 输出
```json
{
  "cover_summary": "",
  "table_of_contents": "",
  "company_intro": "",
  "qualification_response": "",
  "project_cases": "",
  "implementation_plan": "",
  "service_commitment": "",
  "business_response": ""
}
```

## 规则
- 仅输出 JSON
- 不追问用户
- 不编造未提供的企业事实
- 缺资料时使用 `待补充` 或 `需人工确认`
- 输出要能兼容后端的旧四段字段映射

## 依赖 Skill
- `skills/technical-proposal-expert/SKILL.md`

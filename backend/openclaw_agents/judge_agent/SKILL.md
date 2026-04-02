---
name: tender-judge
description: 评估投标可行性，判断是否建议投标，分析风险点
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins: []
      env: []
    emoji: "⚖️"
    homepage: https://github.com/zhihuigu/tender
---

# 投标决策评估

基于招标文件和企业知识库，评估投标可行性。

## 功能

- 评估企业资质与招标要求的匹配度
- 分析预算合理性和竞争情况
- 识别潜在风险
- 给出投标建议

## 输入

1. 招标文件字段（JSON）
2. 企业资质知识
3. 企业案例知识

## 输出

```json
{
  "should_bid": true,
  "reason": "判断理由详细说明",
  "risks": ["风险点1", "风险点2"]
}
```

## 判断标准

### 建议投标 (should_bid: true)

- 企业资质完全或大部分满足招标要求
- 预算在企业能力范围内
- 有相关项目经验
- 风险可控

### 不建议投标 (should_bid: false)

- 资质明显不匹配
- 预算低于企业成本
- 缺乏相关经验
- 风险过高

## 风险类型

- **资质风险**: 缺少必要资质
- **预算风险**: 预算不足或过低
- **技术风险**: 技术要求超出能力
- **时间风险**: 工期紧张
- **竞争风险**: 竞争对手强大
- **信息风险**: 知识库信息不足

## 知识来源

- `qualifications`: 企业资质证书
- `project_cases`: 过往成功案例

## 示例

输入：
```json
{
  "qualification_requirements": ["CMMI5", "ISO27001"],
  "budget": "500万"
}
```

企业资质：["CMMI5", "ISO9001"]

输出：
```json
{
  "should_bid": true,
  "reason": "企业具备CMMI5认证，满足主要资质要求。预算500万在合理范围内。",
  "risks": ["缺少ISO27001认证，可能影响评分", "需要确认具体评分标准"]
}
```

## 依赖 Skills

- `json-toolkit` - JSON 处理
- `context-gatekeeper` - 上下文管理
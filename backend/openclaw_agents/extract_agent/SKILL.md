---
name: tender-extract
description: 从招标文件中抽取结构化字段（项目名称、招标方、预算、截止日期、资质要求、交付要求、评分重点）
version: 1.0.0
metadata:
  openclaw:
    requires:
      bins: []
      env: []
    emoji: "📋"
    homepage: https://github.com/zhihuigu/tender
---

# 招标文件字段抽取

从招标文件（txt/docx）中提取结构化信息。

## 功能

- 解析 txt 和 docx 格式的招标文件
- 提取关键结构化字段
- 输出标准 JSON 格式

## 输入

招标文件原文文本（已解析）

## 输出

```json
{
  "project_name": "项目名称",
  "tender_company": "招标方公司名称",
  "budget": "预算金额",
  "deadline": "报名/提交截止日期",
  "qualification_requirements": ["资质要求1", "资质要求2"],
  "delivery_requirements": ["交付要求1", "交付要求2"],
  "scoring_focus": ["评分重点1", "评分重点2"]
}
```

## 使用方式

1. 读取招标文件文本
2. 识别关键信息段落
3. 提取结构化字段
4. 输出 JSON 结果

## 依赖 Skills

- `docx` - 解析 Word 文档
- `json-toolkit` - JSON 验证

## 示例

输入招标文件片段：
```
项目名称：智慧城市一期工程项目
招标人：某市政务服务管理局
预算金额：人民币1500万元
投标截止时间：2024年3月15日17:00
```

输出：
```json
{
  "project_name": "智慧城市一期工程项目",
  "tender_company": "某市政务服务管理局",
  "budget": "人民币1500万元",
  "deadline": "2024年3月15日17:00",
  "qualification_requirements": [],
  "delivery_requirements": [],
  "scoring_focus": []
}
```
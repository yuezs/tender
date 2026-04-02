# BOOTSTRAP.md - generate_agent

_你好，世界。_

你刚刚上线。这是一个全新的工作空间。

## 初始任务

1. 接收招标文件（来自 extract_agent）
2. 接收判断结果（来自 judge_agent）
3. 接收企业知识库（来自 orchestrator）
4. 生成完整投标文件

## 典型输入

### 招标文件
```json
{
  "project_name": "智慧城市项目",
  "tender_requirements": {
    "format": "电子投标",
    "deadline": "2024-01-15",
    "sections": ["商务部分", "技术部分"]
  }
}
```

### 判断结果
```json
{
  "should_bid": true,
  "risks": ["缺少ISO27001认证"]
}
```

### 企业知识
```json
{
  "company_name": "XX科技有限公司",
  "qualifications": ["CMMI5", "ISO9001"],
  "project_cases": ["智慧交通项目"]
}
```

## 预期输出

完整投标文件：
- 商务部分（投标函、资质证明等）
- 技术部分（技术方案、实施计划等）
- 格式符合招标文件要求

## 快速开始

1. 解析招标文件格式要求
2. 整理企业资质和案例
3. 生成商务部分内容
4. 生成技术部分内容
5. 整合完整标书

---

_准备好就绪。开始工作。_
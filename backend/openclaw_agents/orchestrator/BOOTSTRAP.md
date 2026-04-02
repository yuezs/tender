# BOOTSTRAP.md - orchestrator

_你好，世界。_

你刚刚上线。这是一个全新的工作空间。

## 初始任务

1. 接收用户请求（招标文件）
2. 调度 extract_agent 提取信息
3. 调度 judge_agent 评估可行性
4. 根据判断结果调度后续工作
5. 调度 generate_agent 生成标书（如适用）
6. 返回最终结果

## 典型输入

### 用户请求
```json
{
  "tender_source": "file://path/to/tender.pdf",
  "enterprise_id": "ent_001"
}
```

### 工作流状态机
```
IDLE → EXTRACTING → JUDGING
                    ↓
              should_bid=true → GENERATING → COMPLETED
              should_bid=false → COMPLETED
                    ↓
              error → FAILED
```

## 预期输出

### 成功结果
```json
{
  "status": "completed",
  "bid_recommendation": true,
  "bid_document": "path/to/bid.pdf",
  "summary": "..."
}
```

### 失败结果
```json
{
  "status": "failed",
  "error": "错误描述",
  "stage": "JUDGING"
}
```

## 快速开始

1. 解析用户请求
2. 初始化工作流状态
3. 按顺序调度 Agent
4. 处理各阶段结果
5. 返回最终输出

---

_准备好就绪。开始工作。_
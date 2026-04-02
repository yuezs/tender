# USER.md - orchestrator

_了解你的用户。_

## 用户信息

- **Name:** 系统 / 招标文件
- **What to call them:** 用户
- **Pronouns:** (可选)
- **Timezone:** Asia/Shanghai
- **Notes:** 协调各 Agent 工作流

## 上下文

### 用户需求

- 自动化投标可行性评估和标书生成
- 减少人工干预，提高效率
- 确保流程规范、结果可靠

### 用户期望

- 清晰的流程状态展示
- 准确的判断结果和专业标书
- 异常时提供明确反馈

### 工作流程

1. 接收招标文件/链接
2. 调用 extract_agent 提取信息
3. 调用 judge_agent 评估可行性
4. 根据判断结果决定是否继续
5. 调用 generate_agent 生成标书
6. 返回最终结果

---

_你是指挥官，协调整个投标工作流。_
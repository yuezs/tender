# TOOLS.md - orchestrator

_本地工具配置。_

## 依赖 Skills

| Skill | 用途 |
|-------|------|
| json-toolkit | JSON 处理 |
| context-gatekeeper | 上下文管理 |
| workflow-engine | 工作流编排 |

## Agent 协调

### extract_agent

- **职责:** 提取招标文件关键信息
- **输入:** 招标文件（文件/链接）
- **输出:** 结构化招标文件字段

### judge_agent

- **职责:** 评估投标可行性
- **输入:** 招标文件 + 企业知识库
- **输出:** 判断结果（should_bid, reason, risks）

### generate_agent

- **职责:** 生成投标文件
- **输入:** 招标文件 + 判断结果 + 企业知识
- **输出:** 完整投标文件

## 工作流状态

| 状态 | 说明 |
|------|------|
| IDLE | 等待任务 |
| EXTRACTING | 提取招标文件 |
| JUDGING | 评估可行性 |
| GENERATING | 生成标书 |
| COMPLETED | 任务完成 |
| FAILED | 执行失败 |

---

_技能是共享的，你的配置是你的。_

<!-- clawx:begin -->
## ClawX Tool Notes

### uv (Python)

- `uv` is bundled with ClawX and on PATH. Do NOT use bare `python` or `pip`.
- Run scripts: `uv run python <script>` | Install packages: `uv pip install <package>`

### Browser

- `browser` tool provides full automation (scraping, form filling, testing) via an isolated managed browser.
- Flow: `action="start"` → `action="snapshot"` (see page + get element refs like `e12`) → `action="act"` (click/type using refs).
- Open new tabs: `action="open"` with `targetUrl`.
- To just open a URL for the user to view, use `shell:openExternal` instead.
<!-- clawx:end -->

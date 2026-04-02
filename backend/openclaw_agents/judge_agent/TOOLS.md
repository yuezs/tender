# TOOLS.md - judge_agent

_本地工具配置。_

## 依赖 Skills

| Skill | 用途 |
|-------|------|
| json-toolkit | JSON 处理 |
| context-gatekeeper | 上下文管理 |

## 知识来源

### 必需知识

| 类型 | 来源 | 说明 |
|------|------|------|
| qualifications | knowledge base | 企业资质列表 |
| project_cases | knowledge base | 企业案例列表 |

### 判断标准

1. **资质匹配度**
   - 完全匹配：建议投标
   - 部分匹配：评估风险后建议
   - 不匹配：不建议投标

2. **预算合理性**
   - 预算在企业能力范围内
   - 预算低于成本

3. **竞争分析**
   - 企业优势明显
   - 竞争激烈

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

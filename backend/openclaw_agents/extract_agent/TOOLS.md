# TOOLS.md - extract_agent

_本地工具配置。_

## 依赖 Skills

| Skill | 用途 |
|-------|------|
| docx | 解析 Word 文档 |
| markdown-converter | 文档格式转换 |
| json-toolkit | JSON 验证和处理 |
| json-repair-kit | 修复损坏的 JSON |

## 支持的输入格式

- txt (纯文本)
- docx (Word 文档)

## 输出规范

标准 JSON 格式，字段名称固定：
- project_name (string)
- tender_company (string)
- budget (string)
- deadline (string)
- qualification_requirements (string[])
- delivery_requirements (string[])
- scoring_focus (string[])

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

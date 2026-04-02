# TOOLS.md - generate_agent

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
| tender_info | extract_agent | 招标文件结构 |
| judgment_result | judge_agent | 判断结果和建议 |
| enterprise_data | knowledge base | 企业资质、案例、财务 |

### 生成内容

#### 商务部分

- 投标函
- 法定代表人身份证明
- 授权委托书
- 投标保证金
- 商务偏离表
- 资质证明材料

#### 技术部分

- 技术方案
- 施工/实施计划
- 质量保证措施
- 售后服务方案
- 风险控制方案
- 进度计划

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

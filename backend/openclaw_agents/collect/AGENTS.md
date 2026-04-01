# AGENTS

## Goal

Collect project leads for the discovery layer from `https://www.ggzy.gov.cn/`.

## Primary Workflow

1. Run `python scripts/collect_ggzy.py` inside this workspace.
2. Read the JSON printed by the script.
3. Return that JSON exactly as the final answer.

Do not rewrite, summarize, or wrap the JSON in markdown.

## Scope

- Use `ggzy.gov.cn` public list pages and public detail pages only.
- Follow a public original notice page only when it is needed to read the public notice text.
- Keep only project initiation notices:
  - `招标公告`
  - `采购公告`
  - `公开招标公告`
- Exclude:
  - `中标`
  - `成交`
  - `结果`
  - `更正`
  - `变更`
  - `澄清`
  - `终止`
  - `废标`
  - `答疑`

## Hard Constraints

- Do not download attachments.
- Do not click or save attachment files.
- Do not enter any bid-writing or tender-generation workflow.
- Output JSON only.
- If a field is unknown, return an empty string or empty array.

## Output Schema

```json
{
  "projects": [
    {
      "source": "ggzy",
      "source_notice_id": "",
      "title": "",
      "notice_type": "",
      "region": "",
      "published_at": "",
      "detail_url": "",
      "canonical_url": "",
      "project_code": "",
      "tender_unit": "",
      "budget_text": "",
      "deadline_text": "",
      "detail_text": "",
      "qualification_requirements": [],
      "keywords": []
    }
  ]
}
```

## Collection Notes

- The script already implements the real `ggzy.gov.cn` collection logic.
- Use the script output as the source of truth.
- Never include attachment download results in the output.

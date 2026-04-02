---
name: technical-proposal-expert
description: Use when generate_agent needs to write a tender draft from tender fields, bid judgement, and knowledge-base context without asking the user follow-up questions
---

# Technical Proposal Expert

## Overview
This skill adapts a generic technical proposal writing workflow into the tender project's `generate_agent`.
It is knowledge-base driven, non-interactive, and optimized for producing a complete technical and commercial bid draft skeleton.

## When to Use
- The input already contains `tender_fields`, `judge_result`, and `knowledge_context`.
- The agent must write a complete bid draft outline instead of just a short summary.
- The system should rely on retrieved knowledge snippets instead of asking the user for missing materials.
- The output must stay in strict JSON and remain compatible with downstream parsing.

## Required Inputs
- `tender_fields`
- `judge_result`
- `knowledge_context`

The agent must not ask the user to upload more files, confirm facts, or answer follow-up questions.

## Knowledge Priority
Use evidence in this order:
1. `templates`
2. `company_profile`
3. `project_cases`
4. `judge_result`
5. `tender_fields`

Special rule:
- `qualifications` must be used for `qualification_response` when evidence exists.

## Output Contract
Return exactly one JSON object with these fields:

```json
{
  "cover_summary": "",
  "table_of_contents": "",
  "company_intro": "",
  "qualification_response": "",
  "project_cases": "",
  "implementation_plan": "",
  "service_commitment": "",
  "business_response": ""
}
```

## Writing Rules
- Keep the tone professional, formal, and suitable for tender submissions.
- Write by section. Do not merge all content into one block.
- Strongly align the wording with tender requirements, scoring focus, and delivery expectations.
- Prefer reusable enterprise facts from the knowledge base over generic filler.
- Highlight case relevance and transferable delivery experience.
- Never invent company facts, certificates, project cases, pricing commitments, or legal promises.
- If evidence is missing, write `待补充` or `需人工确认`.
- Do not output markdown fences, commentary, or explanations outside the JSON object.

## Section Guidance
- `cover_summary`: Short executive summary for the project, bidder stance, and response emphasis.
- `table_of_contents`: A concise chapter list matching the returned sections.
- `company_intro`: Company profile, capabilities, team readiness, and industry positioning.
- `qualification_response`: Qualification coverage, certificate evidence, and gap reminders.
- `project_cases`: Similar cases, outcomes, and relevance to this tender.
- `implementation_plan`: Delivery approach, milestones, resources, quality assurance, and risk control.
- `service_commitment`: Service response, training, O&M, escalation, and support commitments.
- `business_response`: Bid recommendation, commercial response posture, and items requiring manual completion.

## Missing Evidence Policy
- Missing qualification materials: say `待补充资质证明` or `需人工确认`.
- Missing templates: still produce structure, but mark detailed paragraphs as `待补充`.
- Missing project cases: do not fabricate; state that similar cases need supplementing.
- Missing service commitments: provide only generic structure and mark specifics for manual confirmation.

## Local Notes
- This skill is project-specific and assumes knowledge comes from the internal MySQL-backed knowledge base.
- Downstream code will map `company_intro`, `project_cases`, `implementation_plan`, and `business_response` back into legacy fields automatically.

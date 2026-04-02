# Technical Proposal Expert Reference

## Intent
This reference records the project-specific constraints that differ from general-purpose proposal writing skills.

## What Was Removed From the External Skill Style
- Interactive question loops
- File-by-file user material collection
- Long-form incremental drafting workflow
- Claude Code specific instructions

## What Was Kept
- Professional proposal tone
- Section-based organization
- Requirement-oriented writing
- Emphasis on case relevance and delivery credibility

## Project Constraints
- Use only the four existing knowledge categories: `company_profile`, `qualifications`, `project_cases`, `templates`
- Do not introduce new agents
- Output must remain JSON-first and parser-friendly
- Missing data must degrade gracefully with `待补充` / `需人工确认`

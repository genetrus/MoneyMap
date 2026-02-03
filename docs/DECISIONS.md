# Decisions

## Template
- Date:
- Title:
- Context:
- Decision:
- Alternatives:
- Consequences:
- Spec reference (PDF + page):
- Owner:

## 2026-02-02 — PDFs are the only requirements source of truth
- Date: 2026-02-02
- Title: PDFs in docs/spec/source are the only requirements source of truth
- Context: The spec defines a staged release plan and Definition of Done that require explicit, testable references for implementation and release gating.
- Decision: Treat only `docs/spec/source/*.pdf` as requirements; use `docs/spec/index.md` for navigation only; require PDF+page citations in decisions/PRs when behavior changes.
- Alternatives: Use README/index as co-equal requirements or allow implicit requirements from chat.
- Consequences: All implementation notes must point to PDF pages; decisions and PRs will carry citations.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.1, p.13–14; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1
- Owner: team

## 2026-02-03 — Always include Prep tasks step and export artifact placeholders
- Date: 2026-02-03
- Title: Always include Prep tasks step and export artifact placeholders
- Context: The MVP plan must include a 4-week outline with steps and artifacts. The walking skeleton referenced artifacts and a Prep tasks step without guaranteeing they were present in exports or steps.
- Decision: Always include a "Prep tasks" step (with a placeholder message when empty) and generate the referenced artifact files during export.
- Alternatives: (1) Hide prep tasks from the 4-week outline when no prep work exists. (2) Remove artifact references from plan output instead of exporting placeholders.
- Consequences: Week plans are consistent, and exported bundles match listed artifacts; users see explicit absence of prep tasks rather than missing steps.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.6–7
- Owner: team

## 2026-02-03 — Quick vs Advanced profile fields and objective preset placement
- Date: 2026-02-03
- Title: Quick vs Advanced profile fields and objective preset placement
- Context: The UX spec calls for a Quick profile entry mode with fewer fields and an Advanced mode with additional fields, and places the objective preset on the Recommendations screen.
- Decision: Implement Quick mode with the five core fields (name, location, language level, capital, time per week) and place objective selection on Recommendations as a preset; Advanced adds assets without inventing new profile fields.
- Alternatives: (1) Add new profile fields not present in the current schema. (2) Keep Quick mode but show all fields and objective on Profile. (3) Move objective into Quick mode.
- Consequences: Quick mode stays lightweight, Advanced adds assets, and objective selection aligns with the Recommendations flow while remaining stored on the profile for scoring.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.8
- Owner: team

## 2026-02-03 — Backlog priority/status mapping for Block 10
- Date: 2026-02-03
- Title: Map MoSCoW requirements to P0/P1/P2 and default status
- Context: The backlog requires P0/P1/P2 priorities and done/next/later statuses, while the spec expresses MoSCoW priorities and does not define current execution status.
- Decision: Map MUST → P0, SHOULD → P1, COULD → P2; leave WON'T out of backlog. Default backlog status is "next" for milestone epics and "later" for gap items until a project tracker provides real status.
- Alternatives: (1) Treat all milestones as P0 without MoSCoW mapping. (2) Infer done/next from repository state.
- Consequences: Backlog priorities reflect spec intent, while status remains neutral pending real tracking.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.5, p.13; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1
- Owner: team

## 2026-02-04 — Block 11 MVP iteration task selection (staleness + DoD tests)
- Date: 2026-02-04
- Title: Select P0 tasks for Block 11 MVP iteration
- Context: Block 11 requires 2–3 P0 tasks that reduce runtime failure risk and advance DoD compliance.
- Decision: Execute T-M3-02-01 (staleness evaluation hardening) and T-M7-01-01 (DoD test coverage) in this iteration.
- Alternatives: (1) Focus on recommendation or plan feature expansion instead of test/validation stability. (2) Split staleness hardening into a separate iteration.
- Consequences: Core CI gains stronger validation/staleness coverage, and validation payloads are stabilized before further UI/feature work.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.7, p.11, p.14
- Owner: team

## 2026-02-04 — Invalid reviewed_at handling for staleness evaluation
- Date: 2026-02-04
- Title: Treat invalid reviewed_at as fatal for rulepack and warning for variants
- Context: Staleness policy requires reliable review dates; missing/invalid dates must surface in validation outputs.
- Decision: When reviewed_at is missing/invalid, staleness evaluation returns severity=fatal and validation raises RULEPACK_REVIEWED_AT_INVALID for rulepack data; variant review_date invalids emit VARIANT_REVIEW_DATE_INVALID warnings and appear in staleness details.
- Alternatives: (1) Treat invalid dates as stale warnings only. (2) Block all recommendations when variant dates are invalid.
- Consequences: Rulepack validity is enforced while variant issues remain actionable warnings without blocking the full dataset.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.7, p.11
- Owner: team

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

## 2026-02-04 — Always include Prep tasks step and export artifact placeholders
- Date: 2026-02-04
- Title: Always include Prep tasks step and export artifact placeholders
- Context: The MVP plan must include a 4-week outline with steps and artifacts. The walking skeleton referenced artifacts and a Prep tasks step without guaranteeing they were present in exports or steps.
- Decision: Always include a "Prep tasks" step (with a placeholder message when empty) and generate the referenced artifact files during export.
- Alternatives: (1) Hide prep tasks from the 4-week outline when no prep work exists. (2) Remove artifact references from plan output instead of exporting placeholders.
- Consequences: Week plans are consistent, and exported bundles match listed artifacts; users see explicit absence of prep tasks rather than missing steps.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.6–7
- Owner: team

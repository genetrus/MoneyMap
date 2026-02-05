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

## 2026-02-04 — Treat unknown variant freshness as require_check for regulated domains
- Date: 2026-02-04
- Title: Regulated legal gating requires re-checks when freshness is unknown
- Context: Regulated recommendations must be cautious when staleness cannot be evaluated due to missing or invalid review dates.
- Decision: When a variant review_date is missing/invalid (non-fatal warning) and the variant is regulated, downgrade legal_gate to require_check and include an explicit DATE_INVALID or DATA_STALE checklist marker. Rulepack reviewed_at invalid remains a validation fatal and stops recommend/plan/export.
- Alternatives: (1) Allow regulated recommendations without extra gating on unknown freshness. (2) Treat unknown freshness as stale without a separate marker. (3) Allow rulepack invalid dates to proceed with warnings.
- Consequences: Regulated options require human verification when variant review dates are invalid, while rulepack invalid dates halt execution to avoid unsafe outputs.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.6–7, p.7, p.11
- Owner: team

## 2026-02-04 — Stop recommend/plan/export when validation has fatals
- Date: 2026-02-04
- Title: Validation fatals halt recommendations, plans, and exports
- Context: DoD requires validation coverage and predictable failures; running critical flows with invalid data undermines reliability.
- Decision: API and CLI operations for recommend/plan/export run validate first and abort with explicit fatals (including RULEPACK_REVIEWED_AT_INVALID) if any are present.
- Alternatives: (1) Proceed with warnings only. (2) Allow recommend/plan/export but tag results as invalid.
- Consequences: Users must fix fatal validation issues before execution, aligning CLI/UI behavior with DoD expectations.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.14
- Owner: team

## 2026-02-05 — Hardening artifacts for run IDs, logs, and validate reports
- Date: 2026-02-05
- Title: Emit run_id-scoped logs and validate reports in exports
- Context: Hardening requires diagnostics, auditability, and clear error handling without stacktraces. The demo checklist needs a consistent place to find validate reports and logs.
- Decision: Each CLI run generates a run_id; logs are written to `exports/logs/<run_id>.log`, and validate reports are written to `exports/validate-report-<run_id>.json`. Error messages include run_id, a hint, and a pointer to the report/log location.
- Alternatives: (1) Print full stacktraces to stderr. (2) Store logs outside exports. (3) Skip validate report files and rely on stdout only.
- Consequences: Users can diagnose runs offline with a stable run_id and file locations, while CLI/UI stays clean.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.6, p.8, p.9, p.11, p.14; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1
- Owner: team

## 2026-02-04 — Data status UI preset styling aligned to UX spec
- Date: 2026-02-04
- Title: Data status UI preset styling aligned to UX spec
- Context: The data status page needs Light/Dark visual presets without changing content or logic. The environment lacks PDF extraction tooling, so the exact UI requirements could not be revalidated directly against the PDFs.
- Decision: Implement CSS-only Light/Dark presets for the Data status page using the existing UI structure, aligning the styling changes to the UX guidance and limiting changes to presentation only.
- Alternatives: (1) Delay the styling updates until PDF text can be extracted. (2) Implement only a single theme.
- Consequences: Visual styling improves while content remains identical; PDF verification remains a follow-up task.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.8
- Owner: team

## 2026-02-06 — Query-param navigation and scoped Data status styling
- Date: 2026-02-06
- Title: Query-param navigation and scoped Data status styling
- Context: Sidebar navigation needed stable selectors and offline-first behavior without relying on aria-labels; Data status styling should not restyle other pages.
- Decision: Use query-param links for sidebar navigation and scope Light/Dark styling to the Data status content while keeping sidebar chrome consistent.
- Alternatives: (1) Keep Streamlit buttons with aria-label selectors. (2) Inject JS to sync navigation state. (3) Apply global theming across all pages.
- Consequences: Navigation stays stable across Streamlit updates/locales, and styling remains isolated to the Data status page.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.8
- Owner: team

## 2026-02-07 — Global Light/Dark theme presets and app-shell styling
- Date: 2026-02-07
- Title: Apply global Light/Dark theme presets and app-shell styling across the UI
- Context: The UI styling regressed to default Streamlit chrome; we need a stable, app-wide theme system that restores the mock-aligned shell while keeping content and logic unchanged. The PDFs do not specify exact visual tokens, so the design alignment is based on the reference mock and kept CSS-only.
- Decision: Introduce global Light/Dark theme presets applied on every render and rebuild the sidebar/navigation chrome with stable `mm-*` hooks. Move the theme switch to a subtle main-header control while keeping all page content and data fields unchanged.
- Alternatives: (1) Keep page-scoped styling limited to Data status. (2) Add JavaScript-driven theming. (3) Leave Streamlit default chrome.
- Consequences: Every page responds to the Light/Dark switch; UI structure remains unchanged while presentation matches the reference mock more closely.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.8
- Owner: team

## 2026-02-08 — Projection-block navigation and centralized projection state
- Date: 2026-02-08
- Title: UI navigation aligned to projection blocks + centralized projection state + filters are not data edits
- Context: Entity/block diagram requires each block to be explicit in UI and data-flow contracts. Existing UI mixed profile/filters/selection keys and hid parts of the block graph.
- Decision: Added 9 block-aligned pages (AppData, UserProfile, Variant, Taxonomy/Cells, Bridges/Paths, RulePack, RecommendationResult, RoutePlan, Exports) and centralized all state transitions in `ui/projection_state.py`. Filters remain user knobs (ranking/selection only), while Variant feasibility/economics/legal stay read-only facts from YAML.
- Alternatives: (1) Keep compact 5-page UI with implicit block mapping. (2) Allow editing Variant facts in User mode.
- Consequences: Dependencies and invalidation are explicit; recommend/plan/export become auditable and deterministic via one projection state graph.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.6–10, p.12
- Owner: team

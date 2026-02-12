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

## 2026-02-05 — Stakeholder "maximum E2E" brief as primary execution baseline
- Date: 2026-02-05
- Title: Use the stakeholder-provided maximum E2E scenario as the primary execution baseline
- Context: The stakeholder provided a detailed end-to-end "maximum" scenario (Profile → Recommendations + Reality Check → Plan → Export) with strict output templates and asked to execute delivery in 20 incremental stages instead of implementing everything at once.
- Decision: Treat the stakeholder-provided maximum E2E scenario as the primary implementation baseline for planning and task sequencing, while enforcing a non-contradiction gate against the PDF specification. When a conflict appears, resolve it by aligning the implementation to the PDF and recording the discrepancy.
- Alternatives: (1) Follow only the minimal PDF framing without using the stakeholder's detailed scenario for backlog decomposition. (2) Treat the stakeholder scenario as optional notes only.
- Consequences: Work can proceed in clear 20-step increments with richer acceptance details and output templates, while still preserving compatibility with MVP boundaries and DoD constraints from the PDF spec.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.3–8, p.13–14
- Owner: team

## 2026-02-10 — MVP приоритезация второстепенных сценариев Explore/Classify
- Date: 2026-02-10
- Title: Treat Explore as SHOULD in MVP UI scope and keep Classify baseline minimal/explainable
- Context: Спецификация фиксирует Explore и Classify как вторичные сценарии, но MoSCoW выделяет MUST/SHOULD/COULD для MVP, где "более богатая классификация" указана как COULD.
- Decision: Для MVP считать Explore частью SHOULD-области UI (browse-режим), а Classify внедрять в базовом, объяснимом и детерминированном виде без усложнений; расширенную классификацию относить к post-MVP backlog.
- Alternatives: (1) Поднять Explore/Classify до MUST и расширить MVP-состав. (2) Полностью отложить оба сценария до post-MVP.
- Consequences: MVP остается в зафиксированных границах, при этом вторичные сценарии внедряются без нарушения MUST-ограничений (offline, deterministic, staleness/legal safety).
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.5, p.8, p.11, p.14
- Owner: team

## 2026-02-10 — DTO-контракты v1 для Explore/Classify/Plan и унификация staleness/legal/evidence
- Date: 2026-02-10
- Title: Introduce DTO contracts VariantCardV1, MiniVariantCard, ClassifyResultV1, PlanTemplateV1
- Context: Для второстепенных сценариев нужны фиксированные контракты данных и единый формат real-world полей, чтобы UI/engine интеграции были совместимыми и объяснимыми.
- Decision: Добавить в `core/model.py` набор DTO-контрактов v1: `VariantCardV1`, `MiniVariantCard`, `ClassifyResultV1` (с `ClassifyCandidate`), `PlanTemplateV1`; а также унифицированные контракты `StalenessContract`, `LegalContract`, `EvidenceContract`.
- Alternatives: (1) Оставить ad-hoc словари в каждом сценарии. (2) Зафиксировать только UI-типизацию без core-контрактов.
- Consequences: Появляется единая точка типизации для Explore/Classify/Plan и единый формат staleness/legal/evidence; дальнейший маппинг в UI/engine можно реализовывать поэтапно без разъезда полей.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.6-7, p.8, p.9-10, p.11, p.14
- Owner: team

## 2026-02-10 — Explore MVP uses deterministic heuristic mapping for cell/taxonomy
- Date: 2026-02-10
- Title: Use tag-based deterministic mapping for Explore Matrix/Taxonomy/Bridges until dedicated datasets are added
- Context: Current data bundle includes `variants.yaml` with tags but no dedicated matrix/taxonomy/bridges source files required for full Explore browse content.
- Decision: Implement Explore baseline with deterministic local heuristics: `tags -> taxonomy` and `tags -> cell`; Bridges use fixed hooks with stable variant ordering (`time_to_first_money_days_range` then `variant_id`).
- Alternatives: (1) Block Explore until dedicated files are available. (2) Add non-deterministic placeholder content.
- Consequences: Explore UI can ship with stable states/tabs and empty-view behavior now; richer content can replace heuristics without changing navigation/state contracts.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.5, p.8, p.9-10, p.11, p.14
- Owner: team


## 2026-02-10 — Temporary Variant A execution mode: skip container UI checks, keep Variant B for later
- Date: 2026-02-10
- Title: Run with Variant A (core/CLI gates only) while container proxy blocks UI installs
- Context: Current container networking enforces a proxy route that returns `Tunnel connection failed: 403 Forbidden` for Streamlit package fetches, so `.[ui]` cannot be installed in the agent runtime even when using `https://pypi.org/simple`.
- Decision: Adopt Variant A as the default execution mode for now: run core/CLI quality gates and explicitly skip container-only UI checks; keep Variant B (full container UI checks) as a deferred path to re-enable once mirror/proxy or wheelhouse transfer is available.
- Alternatives: (1) Block all work until container UI install is possible. (2) Keep retrying UI installs every chat despite known proxy failure.
- Consequences: Delivery can continue without repeated setup loops; UI checks remain an environment-limited gate and must be re-enabled when connectivity artifacts become available.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.11, p.14
- Owner: team


## 2026-02-10 — Classify pipeline v1 uses deterministic keyword/mapping signals from local YAML
- Date: 2026-02-10
- Title: Implement deterministic Classify pipeline with keywords.yaml and mappings.yaml
- Context: Classify requires reproducible text-to-taxonomy/cell outputs with explanations in offline mode. The dataset previously lacked dedicated keyword/mapping files for this flow.
- Decision: Add `data/keywords.yaml` and `data/mappings.yaml` as baseline signal sources and implement pipeline stages: normalization, signal extraction, taxonomy scoring, cell scoring, explanation, and ambiguity mode. Keep tie-breaking deterministic (`score desc`, then `id asc`).
- Alternatives: (1) Delay Classify until richer datasets are available. (2) Use non-deterministic LLM-only heuristics.
- Consequences: Classify becomes reproducible and testable now; richer mappings can be expanded later without changing stage order.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.4, p.8, p.9-10, p.11, p.14
- Owner: team


## 2026-02-10 — Plan markdown renderer upgraded to Plan Template v1 with quota validation
- Date: 2026-02-10
- Title: Enforce Plan Template v1 section order and minimum quotas in plan.md generation
- Context: The new planning flow requires a strict section order with explicit disclaimers, compliance section, and evidence/staleness appendix; generator output must remain actionable and auditable.
- Decision: Replace the legacy plan markdown with Template v1 order (metadata → executive summary → feasibility/blockers → targets → artifacts → checklist → 4-week plan → compliance → economics/tracking → risks → decision points/fallbacks → evidence/staleness) and enforce minimum quotas at render time: `>=10` steps, `>=3` artifacts, mandatory compliance entries.
- Alternatives: (1) Keep old compact plan layout and validate only in tests. (2) Enforce quotas only in graph builder.
- Consequences: plan.md export now has stable structure and guardrails by construction; invalid plans fail fast with explicit errors.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.6-7, p.11, p.14
- Owner: team


## 2026-02-10 — Classify pipeline degrades gracefully when keyword/mapping files are missing
- Date: 2026-02-10
- Title: Treat missing/invalid keywords.yaml or mappings.yaml as non-fatal classify input gaps
- Context: In offline/restricted environments or intermediate dataset states, classification signal files can be absent or malformed. The UI/CLI classify flow should not crash if core data is valid.
- Decision: If `data/keywords.yaml` or `data/mappings.yaml` is missing/invalid, classify falls back to deterministic defaults and appends explicit warning reasons (`*_missing_or_invalid`) to explanations instead of throwing exceptions.
- Alternatives: (1) Fail classify on missing files. (2) Hide classify output without explanation.
- Consequences: Classify remains reproducible and user-visible while transparently signaling degraded confidence/input quality.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.8, p.11, p.14
- Owner: team

## 2026-02-11 — UI startup normalizes empty session profile/filters to defaults
- Date: 2026-02-11
- Title: Prevent Streamlit startup crash when session profile or filters are null
- Context: Session defaults define `profile` as `None`; on startup `_init_state()` read `st.session_state["profile"].get(...)`, which crashes if persisted state contains null profile.
- Decision: Normalize `profile` and `filters` in `_init_state()` so non-dict values are replaced with defaults and partial dicts are merged with default keys before any `.get(...)` access.
- Alternatives: (1) Keep `setdefault()` only and require manual state reset by users. (2) Wrap `.get` call with a local `if profile is None` branch only.
- Consequences: App startup becomes resilient to stale/corrupted session state and backward-compatible with older state payloads.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.8, p.11, p.14
- Owner: team

## 2026-02-12 — Add DE/BY/MUC seed data-pack scaffold under data/packs/de_muc
- Date: 2026-02-12
- Title: Add `data/packs/de_muc` scaffold with regional metadata and seed files
- Context: We need a region-scoped seed pack layout for Munich (`DE/BY/MUC`) while keeping compatibility with current core dataset artifacts (`data/meta.yaml`, `data/rulepacks/DE.yaml`, `data/variants.yaml`).
- Decision: Create `data/packs/de_muc/` with `meta.yaml`, `rulepack.yaml`, `occupation_map.yaml`, `variants.seed.yaml`, `bridges.seed.yaml`, and `routes.seed.yaml`; keep seed collections empty (`[]`) and encode explicit dependencies on core files in pack metadata.
- Alternatives: (1) Reuse top-level `data/*` files without a regional pack folder. (2) Populate non-empty placeholder seed entries not grounded in current verified sources.
- Consequences: Regional pack structure exists for ingestion/expansion, and dependency links to core artifacts are explicit without inventing unverified content.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.9-10, p.15; Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.2
- Owner: team

## 2026-02-12 — Populate de_muc variants.seed with A1..P4 recommendation-ready synthetic coverage
- Date: 2026-02-12
- Title: Fill `data/packs/de_muc/variants.seed.yaml` with balanced multi-cell seed variants
- Context: The Munich pack scaffold had an empty variants seed, which prevented matrix-wide recommendation/prototyping scenarios for expanded cells A1..P4.
- Decision: Generate 768 deterministic seed variants (`12` per cell across `A1..P4`) with filled `tags`, `feasibility`, `legal.gate`, `time_to_first_money_days`, `confidence`, and `sources`; rotate work modes across employment, services, hybrid, and micro-product to keep recommendation candidates diverse.
- Alternatives: (1) Fill only a subset of cells and leave sparse coverage. (2) Add free-form records without consistent required fields.
- Consequences: The pack now supports broad plan/recommendation sampling over the full matrix while preserving consistent minimum data fields per variant.
- Spec reference (PDF + page): Money_Map_Spec_Packet.pdf p.9-10, p.14-15; Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.2
- Owner: team

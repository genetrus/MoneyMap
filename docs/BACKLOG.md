# Money Map Backlog

Canonical backlog: `docs/backlog.yaml`.

## Incremental execution checklist (20-stage baseline)

Current focus (4 stages requested by stakeholder):

- [x] **Stage 1 — E2E frame + DoD lock**: confirm target flow (`Data status → Profile → Recommendations → Plan → Export`) and fix explicit completion criteria. See `docs/releases/STAGE_01_E2E_DOD.md`.
- [x] **Stage 2 — AppData loading foundation**: load local YAML/JSON dataset, `meta.yaml` and DE rulepack into unified app data before recommendation flows. See `docs/releases/STAGE_02_APPDATA_LOADING.md`.
- [x] **Stage 3 — `validate(AppData)` implementation**: add refs/enums/min-semantic checks with `FATAL/WARN` report output and status derivation. See `docs/releases/STAGE_03_VALIDATE_APPDATA.md`.
- [x] **Stage 4 — staleness policy**: implement `warn_after_days`/`hard_after_days` and stale/hard-stale flags in core staleness evaluation. See `docs/releases/STAGE_04_STALENESS_POLICY.md`.
- [x] **Stage 5 — Data status screen**: implement UI for versions, reviewed_at, WARN/FATAL counters, stale alerts, and safe scenario entry without crashes. See `docs/releases/STAGE_05_DATA_STATUS_SCREEN.md`.

## Requirements summary (from PDFs)
- Product is an offline-first tool that recommends income options per country/profile; deliverable as Python package with Typer CLI and Streamlit UI. Spec refs: Money_Map_Spec_Packet.pdf p.1, p.3.
- Output includes ranked Top-N variants with feasibility, legal gate, time-to-first-money, net income ranges (no promises). Spec refs: Money_Map_Spec_Packet.pdf p.3-4, p.6-7.
- User flow: profile → top-10 recommendations → select → plan with steps/artefacts/4-week calendar → export. Spec refs: Money_Map_Spec_Packet.pdf p.4, p.6, p.8.
- Exports must include plan.md, result.json, profile.yaml. Spec refs: Money_Map_Spec_Packet.pdf p.3, p.10.
- MVP scope is Germany-only with YAML/JSON dataset, validation, objective presets, feasibility/economics/legal layers, route plan, and Streamlit UI. Spec refs: Money_Map_Spec_Packet.pdf p.5-6.
- Recommendation engine must be deterministic, objective-driven, and provide explanations/diagnostics. Spec refs: Money_Map_Spec_Packet.pdf p.6.
- Feasibility engine outputs feasible/with_prep/not_feasible with blockers, prep steps, and estimated weeks. Spec refs: Money_Map_Spec_Packet.pdf p.6-7.
- Economics snapshot requires time-to-first-money and net ranges, plus volatility/costs/confidence. Spec refs: Money_Map_Spec_Packet.pdf p.7.
- Legal gate must output ok/require_check/registration/license/blocked with concrete checklists and compliance kits; staleness warnings apply. Spec refs: Money_Map_Spec_Packet.pdf p.7, p.11.
- UI screens: Data status, Profile, Recommendations with Reality Check, Plan, Export, Explore. Spec refs: Money_Map_Spec_Packet.pdf p.8.
- Data entities include Variant, UserProfile, RulePack, Bridge/Path, RecommendationResult, RoutePlan; data stored locally (YAML/JSON) with Streamlit session state. Spec refs: Money_Map_Spec_Packet.pdf p.9-10.
- NFRs: offline-only, safe_load (no eval/exec), auditability via applied rules in exports, performance targets for validate/recommend. Spec refs: Money_Map_Spec_Packet.pdf p.11.
- Architecture is layered (data → core → render → interfaces) with core independent from UI/CLI. Spec refs: Money_Map_Spec_Packet.pdf p.12.
- Release plan milestones M0–M7 define the MVP path. Spec refs: Money_Map_Spec_Packet.pdf p.13.
- Definition of Done requires E2E UI flow, determinism, staleness behavior, and CI running pytest + validate. Spec refs: Money_Map_Spec_Packet.pdf p.14.
- Patch Pack v1 requires meta.yaml with dataset_version + staleness_policy, DE rulepack, variant extensions, and engines plus UI Reality Check. Spec refs: Money_Map_Spec_Packet.pdf p.15.
- Data program requires inventory, dictionary, ER, producer/consumer matrix, policies, seed/fixture packs, and data contract tests. Spec refs: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1-2.
- Development checklist includes backlog decomposition into Epic → Story → Task with priority. Spec refs: Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1.

## Legend
- **Priority**: P0 = must-have (MVP / milestone blocker), P1 = should-have (next iteration), P2 = nice-to-have.
- **Status**: done / next / later.

## Milestones (M0–M7) and epic mapping
| Milestone | Description (spec) | Epic |
| --- | --- | --- |
| M0 | Repo skeleton, CLI/UI stubs, CI; `pip install -e .`, `money-map --help`, `money-map ui` works. | E-M0 |
| M1 | Golden dataset v0 + meta + DE rulepack; load+validate; taxonomy/cells visible. | E-M1 |
| M2 | Query/search + indexes; search returns relevant results. | E-M2 |
| M3 | Legal gate + compliance builder + staleness; check outputs gate+checklist; stale warns. | E-M3 |
| M4 | Feasibility + Economics + recommend objectives; top-10 sensible with reasons and ranges. | E-M4 |
| M5 | RoutePlan + 4-week plan + exports; plan.md includes steps/artefacts/compliance. | E-M5 |
| M6 | Streamlit UI MVP E2E flow (Profile → Recommendations → Plan → Export). | E-M6 |
| M7 | Stabilization: tests, CI, content; pytest green and demo profiles stable. | E-M7 |

## Epic E-M0 — Repo scaffold, CLI/UI stubs, CI baseline
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.13; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1.

### Story S-M0-01 — Repository skeleton and packaging
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.13.
- **Acceptance criteria**:
  - Editable install works and package metadata is defined.

**Tasks**
- **T-M0-01-01** — Define package layout and metadata (src/ layout, scripts)
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.13.
  - Acceptance criteria: Project installs with `pip install -e .` and exposes the package.
  - Repo touches: []
- **T-M0-01-02** — Wire CLI entrypoint for help output
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.13.
  - Acceptance criteria: `money-map --help` responds without errors.
  - Repo touches: []

### Story S-M0-02 — UI stub and CI quality gates
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.13; Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1.
- **Acceptance criteria**:
  - UI stub launches and CI runs format/lint/tests gates.

**Tasks**
- **T-M0-02-01** — Create Streamlit UI stub entrypoint
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.13; Money_Map_Spec_Packet.pdf p.1.
  - Acceptance criteria: `money-map ui` opens a basic Streamlit screen.
  - Repo touches: []
- **T-M0-02-02** — Set up CI with format, lint, and tests
  - Priority: P0 | Status: next
  - Spec refs: Блок-схема_старт_разработки_A4_FINAL_v3.pdf p.1.
  - Acceptance criteria: CI executes formatting, linting, and test steps on push/PR.
  - Repo touches: []

## Epic E-M1 — Golden dataset v0, meta, DE rulepack, load/validate
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6-7, p.9, p.13, p.15; Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1-2.

### Story S-M1-01 — Data inventory, dictionary, and relationships
- **Priority**: P0
- **Status**: next
- **Spec refs**: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1.
- **Acceptance criteria**:
  - Data inventory, dictionary, ER, producer/consumer matrix, and policies are documented.

**Tasks**
- **T-M1-01-01** — Compile data inventory covering use cases, UX, and runtime data
  - Priority: P0 | Status: next
  - Spec refs: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1.
  - Acceptance criteria: Every data item is listed with category and purpose.
  - Repo touches: []
- **T-M1-01-02** — Define data dictionary (types, sources, rules, PII)
  - Priority: P0 | Status: next
  - Spec refs: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1.
  - Acceptance criteria: Each field has type, source, validation, and PII classification.
  - Repo touches: []
- **T-M1-01-03** — Document ER relationships and producer/consumer matrix
  - Priority: P0 | Status: next
  - Spec refs: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1.
  - Acceptance criteria: ER relationships and producer/consumer ownership are explicit for all data items.
  - Repo touches: []
- **T-M1-01-04** — Define data policies (roles, retention, access, contracts)
  - Priority: P0 | Status: next
  - Spec refs: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1.
  - Acceptance criteria: Policies cover permissions, retention, and data contracts.
  - Repo touches: []

### Story S-M1-02 — Seed dataset, meta, rulepack, and validation
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6-7, p.15; Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.2.
- **Acceptance criteria**:
  - Golden dataset v0 loads and validates for DE with rulepack and meta.

**Tasks**
- **T-M1-02-01** — Create dataset meta with versioning and staleness policy
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.15.
  - Acceptance criteria: meta.yaml includes dataset_version and staleness_policy.
  - Repo touches: []
- **T-M1-02-02** — Build DE rulepack with legal gates and compliance kits
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6-7, p.15.
  - Acceptance criteria: Rulepack defines legal gate statuses and compliance kit outputs.
  - Repo touches: []
- **T-M1-02-03** — Populate variants with feasibility, economics, legal, and review dates
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6-7, p.15.
  - Acceptance criteria: Each variant includes feasibility/economics/legal fields and reviewed_at.
  - Repo touches: []
- **T-M1-02-04** — Implement dataset validation with FATAL/WARN reporting
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6.
  - Acceptance criteria: Validation reports issues with severity and semantic checks.
  - Repo touches: []

## Epic E-M2 — Query/search and exploration
- **Priority**: P1
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.13; Money_Map_Spec_Packet.pdf p.8.

### Story S-M2-01 — Search/query API with indexes
- **Priority**: P1
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.13.
- **Acceptance criteria**:
  - Search returns relevant results across taxonomy, cells, and tags.

**Tasks**
- **T-M2-01-01** — Build indexes for taxonomy, cells, tags, and keywords
  - Priority: P1 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.13.
  - Acceptance criteria: Indexes enable fast lookup by taxonomy/cell/tag.
  - Repo touches: []
- **T-M2-01-02** — Expose search in CLI/UI with relevance ordering
  - Priority: P1 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.13.
  - Acceptance criteria: CLI/UI search returns ordered, explainable results.
  - Repo touches: []

### Story S-M2-02 — Explore mode (matrix, taxonomy graph, bridges/paths)
- **Priority**: P1
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.8.
- **Acceptance criteria**:
  - Explore view supports browsing matrix, taxonomy graph, and routes.

**Tasks**
- **T-M2-02-01** — Render matrix and taxonomy graph views
  - Priority: P1 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.8.
  - Acceptance criteria: Users can browse the 2x2x2 matrix and taxonomy graph.
  - Repo touches: []
- **T-M2-02-02** — Add bridges/paths explorer with filters
  - Priority: P1 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.8.
  - Acceptance criteria: Routes can be filtered and inspected without running a recommendation.
  - Repo touches: []

## Epic E-M3 — Legal gate, compliance kits, staleness
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6-7, p.13.

### Story S-M3-01 — Legal evaluation and compliance kits
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6-7.
- **Acceptance criteria**:
  - Each variant yields legal gate status with checklists and kits.

**Tasks**
- **T-M3-01-01** — Implement legal_gate statuses and checklist rendering
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.7.
  - Acceptance criteria: Legal gate output includes ok/require_check/registration/license/blocked.
  - Repo touches: []
- **T-M3-01-02** — Surface compliance kits in outputs and exports
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.7.
  - Acceptance criteria: Compliance kits (tax, invoicing, insurance) appear in plan/results.
  - Repo touches: []

### Story S-M3-02 — Staleness policy enforcement
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.7, p.11.
- **Acceptance criteria**:
  - Stale data triggers warnings and cautious legal gating.

**Tasks**
- **T-M3-02-01** — Calculate staleness from reviewed_at and policy
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.7, p.11.
  - Acceptance criteria: Staleness evaluation returns status and warning metadata.
  - Repo touches: []
- **T-M3-02-02** — Force require_check when data is stale for regulated domains
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.6-7.
  - Acceptance criteria: Regulated domains downgrade legal gate to require_check when stale.
  - Repo touches: []
- **T-M3-02-03** — Treat invalid/missing reviewed_at as unknown freshness for regulated gating
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.6-7, p.7, p.11.
  - Acceptance criteria:
    - Invalid/missing variant review_date forces regulated legal_gate=require_check.
    - Rulepack reviewed_at invalid remains a validation fatal and stops recommend/plan/export.
    - Checklist includes DATA_STALE or DATE_INVALID marker for unknown freshness.
  - Repo touches: []

## Epic E-M4 — Feasibility, economics, recommendation objectives
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6-7, p.13.

### Story S-M4-01 — Feasibility engine with blockers and prep steps
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6-7.
- **Acceptance criteria**:
  - Feasibility status includes blockers, prep steps, and prep duration.

**Tasks**
- **T-M4-01-01** — Compute feasibility status and top 3 blockers
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6-7.
  - Acceptance criteria: Outputs are feasible/feasible_with_prep/not_feasible with max 3 blockers.
  - Repo touches: []
- **T-M4-01-02** — Generate prep steps and estimated prep weeks range
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.7.
  - Acceptance criteria: Prep steps include concrete actions and estimated weeks range.
  - Repo touches: []

### Story S-M4-02 — Economics snapshot with ranges and confidence
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6-7.
- **Acceptance criteria**:
  - Economics includes time-to-first-money, net range, costs, and confidence.

**Tasks**
- **T-M4-02-01** — Compute time_to_first_money and net_month ranges
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.7.
  - Acceptance criteria: Economics snapshot uses ranges (not promises) for money/time.
  - Repo touches: []
- **T-M4-02-02** — Add volatility, costs, scaling ceiling, and confidence
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.7.
  - Acceptance criteria: Economics snapshot includes volatility, costs, scaling ceiling, confidence.
  - Repo touches: []

### Story S-M4-03 — Recommendation engine with objectives and explanations
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6.
- **Acceptance criteria**:
  - Ranking is deterministic, objective-driven, and explainable.

**Tasks**
- **T-M4-03-01** — Implement candidate filtering, scoring, and deterministic tie-breakers
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6.
  - Acceptance criteria: Top-N results are stable for identical inputs.
  - Repo touches: []
- **T-M4-03-02** — Return explanations (3 pros, 1-2 cons) and diagnostics
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6.
  - Acceptance criteria: Each result lists explanations and diagnostics of filters applied.
  - Repo touches: []

## Epic E-M5 — Route plan, 4-week plan, exports
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6, p.10, p.13.

### Story S-M5-01 — Route plan and 4-week launch plan
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6.
- **Acceptance criteria**:
  - Route plan provides steps, artifacts, checklists, and 4-week view.

**Tasks**
- **T-M5-01-01** — Generate route steps from bridges/paths with artifacts
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6.
  - Acceptance criteria: Route steps list outputs/artifacts per step.
  - Repo touches: []
- **T-M5-01-02** — Build 4-week plan and aggregated compliance checklist
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.6.
  - Acceptance criteria: Plan includes 4-week schedule and aggregated checklist.
  - Repo touches: []

### Story S-M5-02 — Export deliverables
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.3, p.10.
- **Acceptance criteria**:
  - plan.md, result.json, and profile.yaml export with required sections.

**Tasks**
- **T-M5-02-01** — Export plan.md with steps, compliance, and artifacts
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.3, p.6.
  - Acceptance criteria: plan.md includes steps, checklists, and compliance section.
  - Repo touches: []
- **T-M5-02-02** — Export result.json and profile.yaml with applied rules
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.3, p.11.
  - Acceptance criteria: result.json includes applied_rules for auditability.
  - Repo touches: []

## Epic E-M6 — Streamlit UI MVP flow
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.8, p.13.

### Story S-M6-01 — Profile → Recommendations → Plan → Export flow
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.8.
- **Acceptance criteria**:
  - UI provides required screens with state handling and data status.

**Tasks**
- **T-M6-01-01** — Implement Data status and Profile entry screens
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.8.
  - Acceptance criteria: Data status shows dataset_version, reviewed_at, warnings.
  - Repo touches: []
- **T-M6-01-02** — Implement Recommendations, Plan, Export screens and transitions
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.8.
  - Acceptance criteria: Flow proceeds without errors from profile to export.
  - Repo touches: []

### Story S-M6-02 — Reality Check block and quick fixes
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.4, p.8.
- **Acceptance criteria**:
  - Reality Check shows top blockers and quick fixes.

**Tasks**
- **T-M6-02-01** — Display top 3 blockers and explanations
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.8.
  - Acceptance criteria: Reality Check lists top blockers based on current profile.
  - Repo touches: []
- **T-M6-02-02** — Implement quick-fix actions and objective presets
  - Priority: P0 | Status: next
  - Spec refs: Money_Map_Spec_Packet.pdf p.8.
  - Acceptance criteria: Quick-fix buttons adjust filters/objective presets.
  - Repo touches: []

## Epic E-M7 — Stabilization: tests, CI, demo content
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.13-14.

### Story S-M7-01 — Definition of Done tests and CI
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.14.
- **Acceptance criteria**:
  - CI runs required tests and validates data.

**Tasks**
- **T-M7-01-01** — Implement DoD tests (validate, feasibility, economics, rules, objectives)
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.14.
  - Acceptance criteria: Test suite covers validation, engines, and UI import smoke tests.
  - Repo touches: []
- **T-M7-01-03** — Add UI import smoke test
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.14.
  - Acceptance criteria: UI modules import without executing Streamlit runtime.
  - Repo touches: []
- **T-M7-01-02** — Ensure CI runs pytest and money-map validate
  - Priority: P0 | Status: done
  - Spec refs: Money_Map_Spec_Packet.pdf p.14.
  - Acceptance criteria:
    - CI executes python -m pytest -q on ubuntu and windows.
    - CI executes python -m money_map.app.cli validate --data-dir data after editable install.
  - Repo touches: []

### Story S-M7-02 — Demo profiles and fixture data
- **Priority**: P0
- **Status**: next
- **Spec refs**: Money_Map_Spec_Packet.pdf p.14; Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.2.
- **Acceptance criteria**:
  - Fixture packs and demo profiles support stable E2E runs.

**Tasks**
- **T-M7-02-01** — Create fixture pack (5-20 variants) for dev/QA/e2e
  - Priority: P0 | Status: next
  - Spec refs: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.2.
  - Acceptance criteria: Fixture pack includes representative variants and profiles.
  - Repo touches: []
- **T-M7-02-02** — Add data contract tests to CI
  - Priority: P0 | Status: next
  - Spec refs: Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.2.
  - Acceptance criteria: CI verifies data contracts for core datasets.
  - Repo touches: []

## Epic E-X — Spec gaps and UX open questions
- **Priority**: P1
- **Status**: later
- **Spec refs**: Money_Map_Spec_Packet.pdf p.8-9; Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf p.1.

### Story S-X-01 — Define taxonomy/cells semantics and mapping guidance
- **Priority**: P1
- **Status**: later
- **Spec refs**: Money_Map_Spec_Packet.pdf p.9.
- **Acceptance criteria**:
  - Taxonomy (14 mechanisms) and 8 cells have explicit definitions and mapping rules.

**Tasks**
- **T-X-01-01** — Publish definitions for 14 mechanisms and 8 cells
  - Priority: P1 | Status: later
  - Spec refs: Money_Map_Spec_Packet.pdf p.9.
  - Acceptance criteria: Definitions clarify how variants map to taxonomy and cells.
  - Repo touches: []
  - Notes: Gap: spec references taxonomy/cells but does not define them in detail.
- **T-X-01-02** — Define bridges/paths semantics and required metadata
  - Priority: P1 | Status: later
  - Spec refs: Money_Map_Spec_Packet.pdf p.9.
  - Acceptance criteria: Bridge/path entries include preconditions and outputs.
  - Repo touches: []
  - Notes: Gap: bridge/path content structure is not detailed.

### Story S-X-02 — Clarify objective presets and quick-fix behaviors
- **Priority**: P1
- **Status**: later
- **Spec refs**: Money_Map_Spec_Packet.pdf p.6, p.8.
- **Acceptance criteria**:
  - Objective presets list and quick-fix adjustments are documented.

**Tasks**
- **T-X-02-01** — Define objective preset list and weight mappings
  - Priority: P1 | Status: later
  - Spec refs: Money_Map_Spec_Packet.pdf p.6.
  - Acceptance criteria: Each preset includes explicit scoring weights and intent.
  - Repo touches: []
  - Notes: Gap: spec requires objective presets but does not define them.
- **T-X-02-02** — Document quick-fix behaviors and filters
  - Priority: P1 | Status: later
  - Spec refs: Money_Map_Spec_Packet.pdf p.8.
  - Acceptance criteria: Quick-fix buttons map to documented filter or objective changes.
  - Repo touches: []
  - Notes: Gap: quick-fix adjustments are named but not specified.

## Gaps / UX issues / Open questions
- **Taxonomy/cells definitions are not explicitly specified** (E-X / S-X-01). Spec refs: Money_Map_Spec_Packet.pdf p.9. See backlog item T-X-01-01.
- **Bridge/path metadata requirements are unclear** (E-X / S-X-01). Spec refs: Money_Map_Spec_Packet.pdf p.9. See backlog item T-X-01-02.
- **Objective presets and quick-fix behaviors lack concrete definitions** (E-X / S-X-02). Spec refs: Money_Map_Spec_Packet.pdf p.6, p.8. See backlog items T-X-02-01 and T-X-02-02.

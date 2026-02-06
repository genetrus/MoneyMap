# Stage 1 — E2E frame + DoD lock

## Scope
This document fixes the MVP end-to-end frame and Definition-of-Done gate for the first stage of incremental execution.

## Target E2E flow (fixed order)
1. **Data status** — dataset/rulepack versions, validation status, and staleness warnings are visible.
2. **Profile** — user fills minimum profile fields required for recommendation.
3. **Recommendations** — system returns deterministic Top-N with feasibility, economics, legal gate, and explanations.
4. **Plan** — user selects one variant and receives an actionable plan with steps, artifacts, and 4-week structure.
5. **Export** — system exports `plan.md`, `result.json`, and `profile.yaml`.

## DoD criteria for Stage 1 (unambiguous)
A Stage 1 implementation is considered ready only when all checks below are true:

- [ ] E2E navigation path exists in UI without stacktrace: `Data status -> Profile -> Recommendations -> Plan -> Export`.
- [ ] Recommendations output includes the three realism layers for each top variant:
  - [ ] Feasibility status (`feasible | feasible_with_prep | not_feasible`) plus blockers/prep.
  - [ ] Economics ranges (`time_to_first_money`, `typical_net_month`) with confidence.
  - [ ] Legal gate (`ok | require_check | registration | license | blocked`) with checklist.
- [ ] Recommendations are deterministic for identical inputs (stable ranking/tie-break behavior).
- [ ] Plan contains actionable execution content (steps + artifacts + 4-week structure).
- [ ] Export produces all three MVP files: `plan.md`, `result.json`, `profile.yaml`.
- [ ] Staleness is surfaced to users (warning visible and cautious legal behavior for regulated cases).

## Verification checklist (operator)
Use this checklist when accepting the stage:

1. Run validation gate and confirm data readiness is shown in Data status.
2. Fill a valid profile and move to Recommendations.
3. Re-run recommendations twice with identical inputs and verify ordering is unchanged.
4. Select one variant and open Plan.
5. Export outputs and verify all three files are present.
6. Confirm staleness warning/gating behavior is visible when stale conditions are present.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.4 (E2E user flow and outputs).
- `Money_Map_Spec_Packet.pdf` p.6–7 (recommendation contracts: feasibility/economics/legal, determinism).
- `Money_Map_Spec_Packet.pdf` p.8 (MVP UI screens).
- `Money_Map_Spec_Packet.pdf` p.10 (export artifacts).
- `Money_Map_Spec_Packet.pdf` p.14 (Definition of Done and test expectations).

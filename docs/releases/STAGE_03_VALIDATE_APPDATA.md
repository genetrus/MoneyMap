# Stage 3 — validate(AppData)

## Scope
Stage 3 hardens dataset validation so `validate(app_data)` returns a complete `ValidationReport` with explicit `FATAL/WARN` issues and a deterministic overall status.

## Validation contract implemented
- Structural checks:
  - `meta.dataset_version` is required.
  - variants list must be non-empty.
  - `variant_id` must be present and unique.
  - `rulepack.rules[].rule_id` must be present and unique.
- Enum checks (warn-level):
  - `legal.legal_gate` must be one of: `ok | require_check | registration | license | blocked`.
  - `economics.confidence` must be one of: `low | medium | high`.
- Minimal semantic checks (warn-level):
  - economics range fields must be numeric `[min, max]` and ordered.
  - feasibility numeric minimums are non-negative.
  - prep steps presence is checked.
- Reference checks (warn-level):
  - optional `legal.rule_ids[]` references must resolve to known `rulepack.rules[].rule_id` values.
- Existing staleness integration remains in report payload and status derivation.

## Status derivation
- `invalid` if `fatals` is non-empty.
- `stale` if no fatals and rulepack staleness is active.
- `valid` otherwise.

## Ready criteria (Stage 3)
- [ ] `validate(app_data)` emits `ValidationReport` with `fatals`, `warns`, `status`, and staleness payload.
- [ ] refs/enums/min-semantic checks produce stable issue codes.
- [ ] duplicate IDs and missing critical fields are fatal.
- [ ] semantic/enumeration inconsistencies are warnings (unless already covered by fatal guards).

## Spec references
- `Money_Map_Spec_Packet.pdf` p.6 (validation and diagnostics contract).
- `Money_Map_Spec_Packet.pdf` p.9–10 (AppData entities and fields).
- `Money_Map_Spec_Packet.pdf` p.11 (offline-safe data handling posture).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD quality gate around validation behavior).

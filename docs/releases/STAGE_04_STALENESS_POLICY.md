# Stage 4 — Staleness policy

## Scope
Stage 4 introduces a unified core staleness policy with two thresholds:
- `warn_after_days`
- `hard_after_days`

and explicit flags:
- `is_stale`
- `is_hard_stale`

## Implemented policy contract
- `evaluate_staleness(reviewed_at, policy)` now computes both stale levels.
- Behavior:
  - `age_days > warn_after_days` -> `is_stale=True`, severity=`warn`.
  - `age_days > hard_after_days` -> `is_hard_stale=True`, severity=`fatal`.
  - invalid/missing date -> severity from `invalid_severity` argument.
- Guardrail:
  - if `hard_after_days < warn_after_days`, hard threshold is clamped to warn threshold.

## Backward compatibility
- `StalenessPolicy(stale_after_days=...)` is still accepted as an alias for `warn_after_days`.
- Loader supports both old and new policy keys in data files.

## Validation/report impact
- Validation keeps status derivation (`invalid`/`stale`/`valid`) and now distinguishes stale rulepack warnings with:
  - `STALE_RULEPACK`
  - `STALE_RULEPACK_HARD`

## Spec references
- `Money_Map_Spec_Packet.pdf` p.7 (staleness behavior in legal/recommendation context).
- `Money_Map_Spec_Packet.pdf` p.11 (offline reliability and conservative handling).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD consistency and predictable outputs).

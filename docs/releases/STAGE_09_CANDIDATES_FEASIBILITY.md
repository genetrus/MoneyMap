# Stage 9 — Candidates + feasibility pipeline (A+B)

## Scope
Implement recommendation pipeline Stage A+B:
- coarse candidate generation filters,
- feasibility-aware handling (`feasible` / `feasible_with_prep` / `not_feasible`) with blockers and prep signals preserved in outputs.

## Implemented behavior
- Added coarse candidate generation pass in recommendation engine before scoring:
  - excludes regulated candidates when profile constraints request non-regulated domains,
  - excludes candidates with required assets when profile has no assets at all.
- Added feasibility-aware filtering mode:
  - new `filters.exclude_not_feasible` optionally removes `not_feasible` candidates,
  - when not excluded, `not_feasible` candidates remain but are score-penalized and marked in cons.
- Diagnostics now distinguish candidate-stage and feasibility-stage outcomes via reason counters and candidate count.
- UI recommendations filter controls now persist and expose `Exclude not feasible` in session filters.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.6 (recommendation pipeline contracts and deterministic ranking).
- `Money_Map_Spec_Packet.pdf` p.7 (feasibility statuses, blockers, prep reality).
- `Money_Map_Spec_Packet.pdf` p.8 (recommendations UI controls and recompute behavior).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD predictability and diagnostics behavior).

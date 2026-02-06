# Stage 13 — Explanations + diagnostics pipeline (F)

## Scope
Ensure each recommendation includes clear explanations and diagnostics:
- exactly 3 “pro” reasons,
- 1–2 “cons”,
- explicit reasons for filtered-out candidates.

## Implemented behavior
- Added explanation builder to recommendation pipeline:
  - selects top 3 pro reasons based on objective-weighted signals (time/net/legal/feasibility/prep/confidence),
  - enforces 1–2 cons derived from feasibility blockers, legal gate friction, slow start, or missing economics.
- Recommendations now always emit `pros` length=3 and `cons` length in [1,2].
- Candidate filtering diagnostics already record reasons (`constraint_regulated`, `missing_assets_all`, `time_to_money`, `blocked`, `not_feasible`) and remain available in `diagnostics.reasons`.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.6 (explainability and diagnostics in recommendations).
- `Money_Map_Spec_Packet.pdf` p.7 (feasibility/economics/legal as explanation anchors).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD: deterministic + explainable output).

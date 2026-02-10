# Stage 14 — Recommendations UI + Reality Check

## Scope
Implement the Recommendations screen UI with filter controls, Reality Check block, and complete card sections for each recommended variant.

## Implemented behavior
- Filter controls now include Top-N, max time-to-money, and legal/feasibility filters.
- Reality Check shows top blockers and quick-fix buttons that recompute recommendations.
- Each recommendation card renders required sections:
  - Feasibility (status, blockers, prep steps, prep weeks),
  - Economics (time-to-money, net range, costs, volatility, confidence),
  - Legal Gate + Compliance (gate, checklist, kits),
  - Explanations (3 pros, 1–2 cons),
  - Selection action.
- Diagnostics list reasons for filtered-out candidates for explainability.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.8 (Recommendations UI and Reality Check).
- `Money_Map_Spec_Packet.pdf` p.6-7 (recommendation output sections).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD explainability and deterministic flow).

# Stage 15 — Edge-case handling

## Scope
Ensure the Recommendations UI handles edge cases without crashes and always provides a next-step suggestion:
- empty results,
- stale warnings,
- all not-feasible outcomes.

## Implemented behavior
- Empty results:
  - show filtered-out reasons (diagnostics),
  - provide quick-fix buttons (allow not-feasible / allow blocked / extend time window).
- All-not-feasible results:
  - show warning and guidance,
  - offer quick fixes to relax feasibility filters.
- Stale warnings remain visible on cards and legal gate entries.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.8 (Recommendations UI behavior and Reality Check).
- `Money_Map_Spec_Packet.pdf` p.6 (recommendation diagnostics).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD: UI resilience and no-crash flow).

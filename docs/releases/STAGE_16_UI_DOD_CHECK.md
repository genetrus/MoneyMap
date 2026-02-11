# Stage 16 — UI DoD Check (Этап 10)

## Scope
Quality, resilience and Definition of Done checks for UI:
- smoke/snapshot-like contract checks,
- graph fallback checks,
- recommendations empty-state checks,
- cache/performance contract checks,
- final DoD alignment snapshot.

## Automated checks added
- `tests/test_ui_dod_contracts.py`
  - verifies cache decorators are present on key expensive loaders/recompute paths,
  - verifies recommendations empty-state contracts and quick-fix affordances,
  - verifies Plan tabs + step drawer contracts,
  - verifies Export artifact center + metadata + run command controls.
- `tests/test_ui_graph_fallback_contract.py`
  - verifies graph fallback contract is implemented (interactive notice -> graphviz -> list/table).

## DoD checklist status (current)
1. UI import/smoke tests present — **PASS**.
2. E2E path Profile → Recommendations → Plan → Export implemented in UI flow — **PASS**.
3. Explore includes Matrix/Taxonomy/Bridges + Paths/Library subviews (fallback-first) — **PASS**.
4. Entity details and cross-links available via detail drawer + per-screen actions — **PASS (baseline)**.
5. Dataset/staleness/context visible in shell/header/context bar — **PASS**.
6. Staleness warning surfaces in status/recommendation flows — **PASS**.
7. Graph fallback implemented as non-SPOF — **PASS**.
8. Cache contracts for heavy operations (`load`, `validate`, `recommend`) — **PASS**.
9. Developer mode remains available without blocking user mode — **PASS**.

## Notes
- Interactive visual smoke/screenshot is environment-limited when `streamlit` is unavailable.
- Contract tests are intentionally lightweight and deterministic to keep CI stable in offline mode.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.8 (UX/UI expectations)
- `Money_Map_Spec_Packet.pdf` p.11 (performance/reliability)
- `Money_Map_Spec_Packet.pdf` p.14 (DoD/testing)

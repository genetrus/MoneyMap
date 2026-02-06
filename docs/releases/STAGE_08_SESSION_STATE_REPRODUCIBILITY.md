# Stage 8 — Session state + reproducibility

## Scope
Implement stable session-state behavior and reproducibility fields for UI flow transitions and recommendation recomputes.

## Implemented behavior
- Session state now explicitly persists:
  - `profile`
  - `filters`
  - `objective_preset`
  - `profile_hash`
  - `selected_variant_id`
- Added `_sync_profile_session_state(profile)` in UI layer:
  - computes deterministic `profile_hash`,
  - syncs `objective_preset`,
  - clears stale selection/plan/recommendations when profile hash changes.
- Recommendations recompute now uses persisted `objective_preset` and keeps selection stable by resetting `selected_variant_id` when chosen variant is no longer present in ranked results.
- Profile page surfaces the current `profile_hash` for reproducibility/diagnostics.

## Rationale
- Same profile inputs should produce same reproducibility fingerprint and deterministic recommendation context across page transitions.
- State reset on profile-change prevents stale plan/selection leakage after edits.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.6 (deterministic recommendations).
- `Money_Map_Spec_Packet.pdf` p.8 (stable UI flow transitions).
- `Money_Map_Spec_Packet.pdf` p.9-10 (runtime/session state entities).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD predictability/reproducibility behavior).

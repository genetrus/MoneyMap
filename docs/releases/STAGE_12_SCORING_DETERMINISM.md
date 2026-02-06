# Stage 12 — Scoring + determinism pipeline (E)

## Scope
Implement objective-weighted scoring and deterministic ranking for reproducible Top-N outputs.

## Implemented behavior
- Scoring now uses normalized pipeline outputs instead of raw variant payloads:
  - economics snapshot (time/net/confidence),
  - feasibility status + prep estimate,
  - legal gate friction.
- Added objective-preset weight sets:
  - `fastest_money` (time-first bias),
  - `max_net` (net bias),
  - `balanced` (mixed trade-off).
- Tie-break remains deterministic and explicit:
  - sorted by `score desc`, then `variant_id asc`.

## Determinism guarantees
- Same input profile/dataset/objective yields identical ranking and score outputs.
- Tie situations are stable due to fixed secondary key (`variant_id`).

## Spec references
- `Money_Map_Spec_Packet.pdf` p.6 (objective-based recommendation and deterministic behavior).
- `Money_Map_Spec_Packet.pdf` p.7 (economics/feasibility/legal scoring factors).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD reproducibility and stable outputs).

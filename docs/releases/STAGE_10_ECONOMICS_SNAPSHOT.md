# Stage 10 — Economics snapshot pipeline (C)

## Scope
Implement recommendation pipeline Stage C economics snapshot so each candidate receives a normalized economics block:
- first-money range,
- net/month range,
- costs range,
- volatility/seasonality,
- confidence.

## Implemented behavior
- Hardened `assess_economics` in core:
  - normalizes numeric ranges and orders reversed bounds,
  - falls back to `[0,0]` for malformed/missing ranges,
  - accepts `volatility_or_seasonality` and fallback alias `volatility`,
  - normalizes confidence enum to `low|medium|high|unknown` with fallback to `unknown`.
- Recommendation pipeline now emits diagnostics warnings when key economics ranges are unknown (`[0,0]`) for first-money/net/costs.
- Economics block continues to be attached to every ranked candidate via `RecommendationVariant.economics`.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.7 (economics snapshot fields and confidence/ranges).
- `Money_Map_Spec_Packet.pdf` p.6 (recommendation pipeline contracts).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD consistency/diagnostics).

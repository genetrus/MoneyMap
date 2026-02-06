# Stage 11 — Legal gate + compliance pipeline (D)

## Scope
Implement legal pipeline D with robust legal gate evaluation and compliance outputs:
- legal gate (`ok|require_check|registration|license|blocked`),
- actionable checklist,
- compliance kits,
- staleness amplification for regulated domains.

## Implemented behavior
- Legal gate normalization now maps unknown/invalid gate values to `require_check` (safe fallback).
- Legal evaluator now selects compliance kits per context:
  - baseline kits for non-regulated/low-friction scenarios,
  - expanded kits for regulated/high-friction gates (`require_check`, `registration`, `license`, `blocked`).
- Staleness amplification remains enforced for regulated variants:
  - stale or freshness-unknown rulepack/variant forces `require_check`,
  - checklist receives stale/date-invalid warning entries.
- Checklist receives explicit regulatory review line for high-friction gates.
- Plan compliance section now uses legal-selected kits first, then checklist items.
- Result JSON legal section now includes explicit `compliance_kits` list.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.7 (legal gate + compliance checklist behavior).
- `Money_Map_Spec_Packet.pdf` p.11 (staleness caution in legal behavior).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD consistency and diagnostics expectations).

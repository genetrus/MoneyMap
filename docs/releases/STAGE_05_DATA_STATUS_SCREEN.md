# Stage 5 — Data status screen

## Scope
Implement the `Data status` UI screen as a safe entry point for the MVP flow with:
- dataset version and reviewed date,
- validation status with `WARN` and `FATAL` counters,
- stale flag with staleness policy,
- alert strip for `invalid` / `stale`,
- validation report download and diagnostics blocks,
- always-visible disclaimer.

## Implemented behavior
- `Data status` renders the six KPI cards from the canonical UI spec for every view mode:
  - Dataset version, Reviewed at, Status, Warnings, Fatals, Stale (+ staleness policy days).
- Alert strip follows status contract:
  - `invalid` => blocking warning text for unreliable Recommendations/Plan/Export.
  - `stale` => stale warning with cautious behavior line for regulated domains.
  - `valid` => compact success caption.
- Validate report section is always visible and supports JSON download with required keys.
- Validation summary, staleness details, and data sources/diagnostics are always visible.
- Disclaimer remains always visible and uses the exact mandatory Russian text.

## Safety / no-crash entry behavior
- Data status page runs under UI error boundary (`_run_with_error_boundary`) and does not crash on user-visible failures.
- Downstream pages still enforce fatal guardrails (`_guard_fatals`) to block unsafe actions when validation contains FATAL issues.

## Spec references
- `Money_Map_Spec_Packet.pdf` p.8 (Data status UI elements/states).
- `Money_Map_Spec_Packet.pdf` p.11 (staleness warning behavior).
- `Money_Map_Spec_Packet.pdf` p.14 (DoD checks for status flow/disclaimer).
- `Блок-схема_Данные_проекта_Определение_и_Сбор_A4_FINAL_v3.pdf` p.2 (diagnosable errors and reproducibility gate).
- `docs/spec/ui/data_status.md` (canonical page contract used for implementation details).

# MoneyMap — 10-minute demo run

This checklist mirrors the MVP demo flow and Definition of Done expectations.

## CLI demo flow
1) Validate datasets:
```bash
money-map validate --data-dir data
```

2) Recommend top variants:
```bash
money-map recommend --profile profiles/demo_fast_start.yaml --top 10 --objective fastest_money
```

3) Pick top-1 and generate a plan:
```bash
money-map plan --profile profiles/demo_fast_start.yaml --variant-id <variant_id>
```

4) Export artifacts:
```bash
money-map export --profile profiles/demo_fast_start.yaml --variant-id <variant_id> --out exports
```

## UI demo flow
1) Open the UI:
```bash
money-map ui
```
2) Navigate through Profile → Recommendations → Plan → Export.
3) Download `plan.md`, `result.json`, and `profile.yaml`.
4) Confirm the UI shows:
   - Dataset version and reviewed_at.
   - Warnings (including stale data warnings when applicable).
   - Validate report details.

## Quick checks
- Look for a warning when rulepack/variant data is stale.
- Verify the disclaimer/legal gate shows when regulated data is stale.
- Confirm `result.json` contains diagnostics and applied_rules for auditability.

## Troubleshooting
If something goes wrong:
- **Validate report**: look for `exports/validate-report-<run_id>.json` from the CLI output.
- **Staleness warning**: stale/unknown review dates will warn; regulated domains require `require_check`.
- **Logs**: inspect `exports/logs/<run_id>.log` for command, dataset version, and timings.
- **Missing profile/variant**: rerun `money-map recommend` and copy a valid `variant_id`.

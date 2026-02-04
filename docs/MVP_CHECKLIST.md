# MVP Checklist

## 1. Dataset validation gate (CLI)
- **What to verify:** Dataset validation runs and reports valid status with no fatal errors before any flows proceed.
- **How to verify:**
  - `make validate`
  - Or:
    - `python -m pip install -e .`
    - `python -m money_map.app.cli validate --data-dir data`
- **Expected output:**
  - Validation report shows `status: valid` and `fatals: 0`.
- **Spec citation:** Money_Map_Spec_Packet.pdf p.5 (MVP requires validate), p.6 (data loading + validation), p.14 (DoD: validate in CI + manual flow).

## 2. CLI end-to-end flow: recommend → plan → export
- **What to verify:** CLI flow completes from recommendations to plan generation and export artifacts for the demo profile without exceptions.
- **How to verify:**
  - `make mvp` (installs UI deps + runs checks)
  - `python scripts/mvp_check.py`
  - Manual CLI flow (optional):
    1. `python -m money_map.app.cli recommend --profile profiles/demo_fast_start.yaml --top 10 --data-dir data`
    2. `python -m money_map.app.cli plan --profile profiles/demo_fast_start.yaml --variant-id <top-1> --data-dir data`
    3. `python -m money_map.app.cli export --profile profiles/demo_fast_start.yaml --variant-id <top-1> --out exports --data-dir data`
- **Expected output:**
  - Recommendations are produced, plan generation reports ready, and export prints paths for `plan.md`, `result.json`, and `profile.yaml` with artifacts present.
- **Spec citation:** Money_Map_Spec_Packet.pdf p.4 (E2E use case), p.5 (MVP includes recommend/plan/export), p.6 (plan + export artifacts), p.14 (DoD E2E flow).

## 3. UI flow (Profile → Recommendations → Plan → Export)
- **What to verify:** Streamlit UI loads and supports the end-to-end flow without stack traces.
- **How to verify:**
  - `python -m pytest -q tests/test_ui_smoke.py` (requires UI deps).
  - Manual UI flow: `python -m money_map.app.cli ui` then navigate Profile → Recommendations → Plan → Export.
- **Expected output:**
  - UI module imports cleanly; manual flow completes without stack traces.
- **Spec citation:** Money_Map_Spec_Packet.pdf p.6 (Streamlit UI flow), p.8 (UI states), p.14 (DoD UI E2E flow).

## 4. Staleness + regulated legal gating
- **What to verify:** Stale or unknown freshness data produces warnings/markers and regulated variants require `require_check` with explicit checklist markers.
- **How to verify:**
  - `python scripts/mvp_check.py` (staleness/regulated checks are included).
  - `python -m pytest -q tests/test_rulepack_staleness.py tests/test_rules_legal_gate.py tests/test_staleness_policy.py`
- **Expected output:**
  - Stale/invalid dates generate warnings/markers; regulated variants are gated with `require_check` and checklist markers like `DATE_INVALID` or `DATA_STALE`.
- **Spec citation:** Money_Map_Spec_Packet.pdf p.6–7 (legal gate + staleness), p.11 (staleness warnings), p.14 (DoD staleness behavior).

## 5. Determinism (stable top-N ordering)
- **What to verify:** Identical inputs return the same top-N ordering (with tie-breakers applied deterministically).
- **How to verify:**
  - `python scripts/mvp_check.py`
  - `python -m pytest -q tests/test_recommend_deterministic.py`
- **Expected output:**
  - Two runs yield identical ordered variant IDs.
- **Spec citation:** Money_Map_Spec_Packet.pdf p.6 (determinism + tie-breaker), p.14 (DoD determinism).

## 6. Plan actionability + export content
- **What to verify:** Plans include minimum actionability (>=10 steps, >=3 artifacts) and exports contain plan, result, profile, and artifacts.
- **How to verify:**
  - `python scripts/mvp_check.py`
  - `python -m pytest -q tests/test_plan_contains_compliance_and_artifacts.py tests/test_export_writes_files.py`
- **Expected output:**
  - Plan has >=10 steps and >=3 artifacts, includes compliance section, and export writes `plan.md`, `result.json`, `profile.yaml`, plus artifact files.
- **Spec citation:** Money_Map_Spec_Packet.pdf p.3 (deliverables), p.6–7 (plan + artifacts), p.14 (DoD PlanActionability + exports).

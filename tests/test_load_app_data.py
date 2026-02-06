from __future__ import annotations

import json

from money_map.core.load import load_app_data


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_app_data_reads_yaml_seed_data() -> None:
    app_data = load_app_data("data")
    assert app_data.meta.dataset_version
    assert app_data.rulepack.reviewed_at
    assert app_data.variants


def test_load_app_data_reads_json_fallback(tmp_path) -> None:
    _write_json(
        tmp_path / "meta.json",
        {"dataset_version": "1.2.3", "staleness_policy": {"stale_after_days": 45}},
    )
    _write_json(
        tmp_path / "variants.json",
        {
            "variants": [
                {
                    "variant_id": "de.test.variant",
                    "title": "Test Variant",
                    "summary": "Summary",
                    "tags": ["test"],
                    "feasibility": {"status": "feasible"},
                    "prep_steps": ["prep"],
                    "economics": {"typical_net_month_eur_range": [500, 1000]},
                    "legal": {"gate": "ok"},
                    "review_date": "2026-01-01",
                }
            ]
        },
    )
    _write_json(
        tmp_path / "rulepacks" / "DE.json",
        {
            "reviewed_at": "2026-01-01",
            "compliance_kits": {"tax_basics": ["register"]},
            "regulated_domains": ["finance"],
            "rules": [{"rule_id": "R1", "reason": "test"}],
        },
    )

    app_data = load_app_data(tmp_path)

    assert app_data.meta.dataset_version == "1.2.3"
    assert app_data.meta.staleness_policy.stale_after_days == 45
    assert app_data.rulepack.rules[0].rule_id == "R1"
    assert app_data.variants[0].variant_id == "de.test.variant"

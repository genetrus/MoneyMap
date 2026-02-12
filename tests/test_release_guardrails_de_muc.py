from __future__ import annotations

from collections import Counter

import pytest

from money_map.core.load import load_app_data
from money_map.core.profile import validate_profile
from money_map.core.recommend import recommend
from money_map.storage.fs import read_yaml
from money_map.ui.jobs_live import fetch_live_jobs, resolve_jobs_source
from money_map.ui.variant_card import has_income_promise

DEFAULT_PROFILE = {
    "name": "Demo",
    "country": "DE",
    "location": "Berlin",
    "objective": "fastest_money",
    "language_level": "B1",
    "capital_eur": 300,
    "time_per_week": 15,
    "assets": ["laptop", "phone"],
    "skills": ["customer_service"],
    "constraints": ["no_night_shifts"],
}


def test_ui_seed_flows_have_non_empty_defaults(monkeypatch) -> None:
    app_data = load_app_data("data")

    profile_check = validate_profile(DEFAULT_PROFILE)
    assert profile_check["is_ready"], "default profile must be runnable without manual input"

    rec = recommend(
        DEFAULT_PROFILE,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        objective_preset=str(DEFAULT_PROFILE.get("objective", "fastest_money")),
        top_n=10,
    )
    assert rec.ranked_variants

    def _no_live(**_kwargs):
        raise OSError("offline")

    monkeypatch.setattr("money_map.ui.jobs_live.fetch_live_jobs", _no_live)
    rows, meta = resolve_jobs_source(city="Munich", radius_km=25, days=7, size=5, profile="")
    assert rows
    assert meta["source"] in {"cache", "seed"}


def test_each_matrix_cell_has_10_to_12_variants() -> None:
    payload = read_yaml("data/packs/de_muc/variants.seed.yaml")
    variants = payload.get("variants", [])
    counts = Counter(str(item.get("cell_id", "")) for item in variants)

    assert counts, "variants.seed should contain matrix cells"
    assert all(10 <= count <= 12 for count in counts.values())


def test_rulepack_contains_core_munich_de_by_checks() -> None:
    payload = read_yaml("data/packs/de_muc/rulepack.yaml")
    rules = payload.get("rules", [])
    ids = {str(rule.get("id", "")) for rule in rules}

    assert any("gewerbe" in rule_id for rule_id in ids)
    assert any("elster" in rule_id for rule_id in ids)
    assert any("ihk" in rule_id for rule_id in ids)

    assert all((rule.get("applies_to") or {}).get("country") == "DE" for rule in rules)
    munich_rules = [
        rule
        for rule in rules
        if (rule.get("applies_to") or {}).get("state") == "BY"
        and (rule.get("applies_to") or {}).get("city") == "MUC"
    ]
    assert munich_rules


def test_jobs_live_returns_munich_results_when_api_available() -> None:
    try:
        rows = fetch_live_jobs(city="München", radius_km=15, days=7, size=5, profile="service")
    except Exception as exc:  # pragma: no cover - environment/API dependent
        pytest.skip(f"Jobs API unavailable: {exc}")

    if not rows:  # pragma: no cover - API can be empty despite availability
        pytest.skip("Jobs API reachable but returned no rows for München query")

    assert len(rows) >= 1
    assert all("title" in row for row in rows)


def test_economics_blocks_use_ranges_and_safe_disclaimer_only() -> None:
    payload = read_yaml("data/variants.yaml")
    variants = payload.get("variants", [])

    for variant in variants:
        economics = variant.get("economics") or {}

        assert isinstance(economics.get("time_to_first_money_days_range"), list)
        assert isinstance(economics.get("typical_net_month_eur_range"), list)
        assert economics.get("confidence") in {"low", "medium", "high"}
        assert economics.get("source")
        assert economics.get("retrieved_at")
        assert economics.get("disclaimer")
        assert economics.get("hint")

        safe_text = " ".join(
            [
                str(economics.get("hint", "")),
                str(economics.get("disclaimer", "")),
            ]
        )
        assert not has_income_promise(safe_text)

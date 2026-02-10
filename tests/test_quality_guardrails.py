from __future__ import annotations

import socket
from dataclasses import replace

from money_map.core.classify import classify_idea_text
from money_map.core.load import load_app_data
from money_map.core.model import StalenessPolicy
from money_map.render.plan_md import render_plan_md
from money_map.ui.variant_card import build_explore_card_copy, has_income_promise


def _block_network(monkeypatch) -> None:
    def _blocked(*_args, **_kwargs):
        raise RuntimeError("network disabled in test")

    monkeypatch.setattr(socket.socket, "connect", _blocked, raising=True)
    monkeypatch.setattr(socket, "create_connection", _blocked, raising=True)


def test_offline_first_classify_works_with_network_blocked(monkeypatch) -> None:
    _block_network(monkeypatch)
    app_data = load_app_data("data")

    result = classify_idea_text(
        "remote freelance writing for local business",
        app_data=app_data,
        data_dir="data",
    )

    assert result.top3
    assert result.cell_guess


def test_classify_handles_missing_mappings_gracefully(tmp_path) -> None:
    app_data = load_app_data("data")

    result = classify_idea_text(
        "subscription monthly recurring remote",
        app_data=app_data,
        data_dir=tmp_path,
    )

    assert result.top3
    assert any(reason.endswith("missing_or_invalid") for reason in result.reasons)


def test_staleness_warning_for_old_rulepack_sets_require_check() -> None:
    app_data = load_app_data("data")
    strict_policy = StalenessPolicy(warn_after_days=1, hard_after_days=2)
    stale_meta = replace(app_data.meta, staleness_policy=strict_policy)
    stale_rulepack = replace(
        app_data.rulepack,
        reviewed_at="2020-01-01",
        staleness_policy=strict_policy,
    )
    stale_data = replace(app_data, meta=stale_meta, rulepack=stale_rulepack)

    result = classify_idea_text(
        "local errand helper",
        app_data=stale_data,
        data_dir="data",
    )

    assert result.staleness.status in {"warn", "hard"}
    assert result.legal.gate == "require_check"


def test_no_guaranteed_income_wording_in_variant_card_copy() -> None:
    app_data = load_app_data("data")
    variant = app_data.variants[0]
    spoofed = replace(
        variant,
        summary=(
            "Guaranteed stable 500€ monthly, you will definitely earn quickly "
            "without any risks"
        ),
    )

    card = build_explore_card_copy(
        spoofed,
        taxonomy="service_fee",
        cell="A2",
        stale=False,
    )

    assert not has_income_promise(card.one_liner)


def test_plan_template_contains_disclaimers_compliance_and_evidence_block() -> None:
    app_data = load_app_data("data")
    from money_map.core.graph import build_plan

    plan = build_plan(
        profile={
            "country": "DE",
            "language_level": "B1",
            "capital_eur": 200,
            "time_per_week": 10,
            "assets": ["laptop"],
            "constraints": [],
        },
        variant=app_data.variants[0],
        rulepack=app_data.rulepack,
        staleness_policy=app_data.meta.staleness_policy,
    )

    rendered = render_plan_md(plan)
    assert "not guarantees" in rendered
    assert "## 7) Compliance & Legal checks" in rendered
    assert "## Appendix A) Evidence & Staleness" in rendered

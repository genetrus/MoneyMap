from money_map.core.model import Variant
from money_map.ui.variant_card import build_explore_card_copy, has_income_promise


def _variant(summary: str) -> Variant:
    return Variant(
        variant_id="de.test.variant",
        title="Test Variant",
        summary=summary,
        tags=["writing", "remote"],
        feasibility={
            "min_language_level": "B1",
            "min_time_per_week": 8,
            "required_assets": ["laptop", "internet"],
        },
        prep_steps=[
            "Create a super long preparatory step with many many words for limit verification",
            "Second step",
        ],
        economics={
            "time_to_first_money_days_range": [7, 14],
            "typical_net_month_eur_range": [400, 900],
            "confidence": "low",
        },
        legal={
            "legal_gate": "require_check",
            "checklist": ["Check permit requirements immediately"],
        },
        review_date="2026-01-01",
    )


def test_variant_card_copy_enforces_text_limits_and_no_promises() -> None:
    raw_summary = (
        "You will definitely earn with guaranteed stable 100€ income every month by "
        "offering this service very quickly and with no effort at all."
    )
    card = build_explore_card_copy(
        _variant(raw_summary),
        taxonomy="service_fee",
        cell="A2",
        stale=False,
    )

    assert len(card.one_liner) <= 160
    assert not has_income_promise(card.one_liner)

    assert len(card.pros) == 3
    assert all(len(item.split()) <= 12 for item in card.pros)
    assert 1 <= len(card.cons) <= 2
    assert all(len(item.split()) <= 14 for item in card.cons)
    assert all(len(item.split()) <= 10 for item in card.blockers)
    assert all(len(item.split()) <= 10 for item in card.prep_steps)
    assert all(len(item.split()) <= 10 for item in card.legal_checks)


def test_has_income_promise_detects_forbidden_phrases() -> None:
    assert has_income_promise("Guaranteed stable 500€ every month")
    assert not has_income_promise("Estimated range only")

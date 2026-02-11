from dataclasses import dataclass

from money_map.ui.data_status import (
    build_validate_rows,
    filter_validate_rows,
    oldest_stale_entities,
    variants_by_cell,
    variants_by_legal_gate,
)


@dataclass
class _VariantStub:
    legal: dict
    cell: str


def test_build_and_filter_validate_rows() -> None:
    report = {
        "fatals": [{"message": "fatal1", "source": "variants", "location": "v1", "code": "F1"}],
        "warns": [{"message": "warn1", "source": "rulepack", "location": "r1", "code": "W1"}],
    }

    rows = build_validate_rows(report)
    assert len(rows) == 2
    assert len(filter_validate_rows(rows, severity="FATAL")) == 1
    assert len(filter_validate_rows(rows, entity_type="rulepack")) == 1


def test_variants_distributions() -> None:
    variants = [
        _VariantStub(legal={"legal_gate": "ok"}, cell="A1"),
        _VariantStub(legal={"legal_gate": "ok"}, cell="A2"),
        _VariantStub(legal={"legal_gate": "blocked"}, cell="A1"),
    ]

    by_cell = variants_by_cell(variants, cell_resolver=lambda v: v.cell)
    by_gate = variants_by_legal_gate(variants)

    assert {row["label"]: row["count"] for row in by_cell} == {"A1": 2, "A2": 1}
    assert {row["label"]: row["count"] for row in by_gate} == {"blocked": 1, "ok": 2}


def test_oldest_stale_entities_returns_top_sorted() -> None:
    variant_staleness = {
        "v1": {"age_days": 100, "severity": "warn", "is_stale": True},
        "v2": {"age_days": 20, "severity": "ok", "is_stale": False},
        "v3": {"age_days": 250, "severity": "fatal", "is_stale": True},
    }

    rows = oldest_stale_entities(variant_staleness, limit=2)
    assert [row["variant_id"] for row in rows] == ["v3", "v1"]

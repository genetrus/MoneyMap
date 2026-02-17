from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from money_map.ui.data_status import (
    aggregate_pack_metrics,
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


def test_aggregate_pack_metrics_counts_and_staleness(tmp_path: Path) -> None:
    pack = tmp_path / "de_muc"
    pack.mkdir(parents=True)

    (pack / "meta.yaml").write_text(
        yaml.safe_dump({"reviewed_at": "2025-01-01"}, sort_keys=False),
        encoding="utf-8",
    )
    (pack / "rulepack.yaml").write_text(
        yaml.safe_dump(
            {
                "reviewed_at": "2025-02-01",
                "regulated_domains": {
                    "childcare": {"checklist": ["doc1"]},
                    "food": {"checklist": ["doc2"]},
                },
                "rules": [{"rule_id": "r1"}, {"rule_id": "r2"}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (pack / "variants.seed.yaml").write_text(
        yaml.safe_dump(
            {
                "variants": [
                    {
                        "id": "v1",
                        "cell_id": "A1",
                        "regulated_domain": "childcare",
                        "legal": {"legal_gate": "require_check"},
                    },
                    {
                        "id": "v2",
                        "cell_id": "A1",
                        "regulated_domain": "food",
                        "legal": {"legal_gate": "ok"},
                    },
                    {"id": "v3", "cell_id": "B2"},
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (pack / "bridges.seed.yaml").write_text(
        yaml.safe_dump({"bridges": [{"id": "b1"}]}, sort_keys=False),
        encoding="utf-8",
    )
    (pack / "routes.seed.yaml").write_text(
        yaml.safe_dump({"routes": [{"id": "rt1"}, {"id": "rt2"}]}, sort_keys=False),
        encoding="utf-8",
    )

    metrics = aggregate_pack_metrics(
        pack_dir=pack,
        staleness_policy_days=180,
        now=date(2026, 2, 12),
    )

    assert metrics["variants_total"] == 3
    assert metrics["bridges_total"] == 1
    assert metrics["routes_total"] == 2
    assert metrics["rule_checks_total"] == 2
    cells = {row["label"]: row["count"] for row in metrics["variants_per_cell"]}
    assert cells["A1"] == 2
    assert cells["B2"] == 1
    assert cells["P4"] == 0
    assert metrics["oldest_reviewed_at"] == "2025-01-01"
    assert metrics["is_stale"] is True
    assert set(metrics["stale_sources"]) == {"meta.yaml", "rulepack.yaml"}
    assert metrics["regulated_domain_coverage"] == {
        "variants_with_regulated_domain": 2,
        "variants_require_check": 1,
        "variants_with_checklist_coverage": 2,
    }

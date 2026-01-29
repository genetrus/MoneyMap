from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil

from money_map.core.evidence import EvidenceItem, EvidenceRegistry
from money_map.core.load import load_app_data, load_yaml
from money_map.core.model import UserProfile
from money_map.core.recommend import recommend
from money_map.core.reviews import ReviewEntry, ReviewsIndex
from money_map.core.rulepack_authoring import scaffold_rulepack, validate_rulepack_structure
from money_map.core.validate import validate_app_data
from money_map.core.workspace import detect_workspace_conflicts, get_workspace_paths, init_workspace
from money_map.core.yaml_utils import dump_yaml


def test_scaffold_rulepack_valid(tmp_path: Path) -> None:
    out_path = tmp_path / "PL.yaml"
    scaffold_rulepack("PL", out_path, placeholder=True)
    payload = load_yaml(out_path)
    issues = validate_rulepack_structure(payload)
    assert issues == []
    assert payload["is_placeholder"] is True


def test_placeholder_rulepack_requires_evidence() -> None:
    data_dir = Path("data")
    appdata = load_app_data(data_dir, country_code="PL")
    profile = UserProfile.model_validate(
        {
            "country_code": "PL",
            "time_hours_per_week": 10,
            "capital_eur": 300,
            "language_level": "B1",
            "skills": ["communication"],
            "assets": ["laptop"],
            "constraints": [],
            "objective_preset": "fast_start",
            "risk_tolerance": "medium",
            "horizon_months": 6,
            "target_net_monthly_eur": 500,
            "preferred_modes": ["service"],
        }
    )

    regulated_variant = next(
        variant
        for variant in appdata.variants
        if variant.legal.regulated_level != "none" or "regulated" in variant.tags
    )

    reviews = ReviewsIndex(
        reviewed_at=date.today().isoformat(),
        entries=[
            ReviewEntry(
                entity_ref=f"variant:{regulated_variant.variant_id}",
                status="verified",
                verified_at=date.today().isoformat(),
                evidence_refs=[],
            )
        ],
    )
    result_missing = recommend(
        profile,
        appdata,
        top_n=len(appdata.variants),
        reviews=reviews,
        evidence_registry=EvidenceRegistry(items=[]),
    )
    missing_variant = next(
        item
        for item in result_missing.ranked_variants
        if item.variant_id == regulated_variant.variant_id
    )
    assert "reason.review.requires_verification" in missing_variant.blockers

    evidence_registry = EvidenceRegistry(
        items=[
            EvidenceItem(
                evidence_id="ev1",
                title="placeholder",
                type="note",
                related_entities=[f"variant:{regulated_variant.variant_id}"],
            )
        ]
    )
    reviews.entries[0].evidence_refs = ["ev1"]
    result_verified = recommend(
        profile,
        appdata,
        top_n=len(appdata.variants),
        reviews=reviews,
        evidence_registry=evidence_registry,
    )
    verified_variant = next(
        item
        for item in result_verified.ranked_variants
        if item.variant_id == regulated_variant.variant_id
    )
    assert "reason.review.requires_verification" not in verified_variant.blockers


def test_workspace_conflicts_detected(tmp_path: Path) -> None:
    data_dir = Path("data")
    workspace = tmp_path / "workspace"
    init_workspace(workspace)
    paths = get_workspace_paths(workspace)
    variants = load_yaml(data_dir / "variants.yaml")
    assert isinstance(variants, list)
    base = dict(variants[0])
    base["summary_key"] = "variant.overlay.summary"

    (paths.overlay / "variants.yaml").write_text(dump_yaml([base]), encoding="utf-8")
    (paths.overlay / "variants_extra.yaml").write_text(
        dump_yaml([{"variant_id": base["variant_id"]}]), encoding="utf-8"
    )

    conflicts = detect_workspace_conflicts(data_dir, workspace)
    assert any(
        item.entity_ref == f"variant:{base['variant_id']}" and item.conflict_type == "overlay_collision"
        for item in conflicts
    )
    assert any(
        item.entity_ref == f"variant:{base['variant_id']}" and item.conflict_type == "overlay_incomplete"
        for item in conflicts
    )


def test_incremental_validation_matches_full(tmp_path: Path) -> None:
    data_src = Path("data")
    data_dir = tmp_path / "data"
    shutil.copytree(data_src, data_dir)

    full_fatals, full_warns = validate_app_data(data_dir)
    inc_fatals, inc_warns = validate_app_data(data_dir, incremental=True)
    assert full_fatals == inc_fatals
    assert full_warns == inc_warns

    variants_path = data_dir / "variants.yaml"
    content = variants_path.read_text(encoding="utf-8")
    variants_path.write_text(content, encoding="utf-8")

    full_fatals_2, full_warns_2 = validate_app_data(data_dir)
    inc_fatals_2, inc_warns_2 = validate_app_data(data_dir, incremental=True)
    assert full_fatals_2 == inc_fatals_2
    assert full_warns_2 == inc_warns_2

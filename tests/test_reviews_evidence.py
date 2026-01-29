from datetime import date
from pathlib import Path

from money_map.core.evidence import add_file_evidence, validate_registry
from money_map.core.load import load_app_data, load_yaml
from money_map.core.model import UserProfile
from money_map.core.recommend import recommend
from money_map.core.reviews import ReviewEntry, ReviewsIndex
from money_map.core.workspace import init_workspace


def test_review_blocker_for_regulated_variant(tmp_path: Path) -> None:
    data_dir = Path("data")
    appdata = load_app_data(data_dir)
    regulated = next(
        variant
        for variant in appdata.variants
        if variant.legal.regulated_level != "none"
    )
    profile_data = load_yaml(Path("profiles/demo_fast_start.yaml"))
    profile = UserProfile.model_validate(profile_data)

    reviews = ReviewsIndex(reviewed_at=date.today().isoformat(), entries=[])
    result = recommend(profile, appdata, top_n=len(appdata.variants), reviews=reviews)
    entry = next(
        item for item in result.ranked_variants if item.variant_id == regulated.variant_id
    )
    assert "reason.review.requires_verification" in entry.blockers

    verified = ReviewsIndex(
        reviewed_at=date.today().isoformat(),
        entries=[
            ReviewEntry(
                entity_ref=f"variant:{regulated.variant_id}",
                status="verified",
                verified_at=date.today().isoformat(),
                reviewer="QA",
            )
        ],
    )
    result_verified = recommend(
        profile, appdata, top_n=len(appdata.variants), reviews=verified
    )
    entry_verified = next(
        item
        for item in result_verified.ranked_variants
        if item.variant_id == regulated.variant_id
    )
    assert "reason.review.requires_verification" not in entry_verified.blockers


def test_evidence_checksum_validation(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    init_workspace(workspace)
    source = workspace / "source.txt"
    source.write_text("evidence", encoding="utf-8")

    add_file_evidence(workspace, source, "EV_001", title="Proof")

    evidence_file = workspace / "evidence" / "files" / source.name
    evidence_file.write_text("changed", encoding="utf-8")

    fatals, _ = validate_registry(workspace)
    assert any(key == "evidence.checksum_mismatch" for key, _ in fatals)

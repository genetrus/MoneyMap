from pathlib import Path

from money_map.app.api import export_bundle, recommend_variants
from money_map.core.graph import build_plan
from money_map.core.load import load_app_data, load_profile


def test_export_writes_files(tmp_path: Path):
    paths = export_bundle(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.fast.freelance_writer",
        out_dir=tmp_path,
    )

    assert Path(paths["plan"]).exists()
    assert Path(paths["result"]).exists()
    assert Path(paths["profile"]).exists()
    app_data = load_app_data()
    profile = load_profile("profiles/demo_fast_start.yaml")
    variant = next(v for v in app_data.variants if v.variant_id == "de.fast.freelance_writer")
    plan = build_plan(profile, variant, app_data.rulepack)
    for artifact in plan.artifacts:
        assert (tmp_path / artifact).exists()


def test_export_works_outside_top_n(tmp_path: Path):
    app_data = load_app_data()
    top_one = (
        recommend_variants(
            profile_path="profiles/demo_fast_start.yaml",
            objective="fastest_money",
            top_n=1,
        )
        .ranked_variants[0]
        .variant.variant_id
    )
    other_variant = next(v.variant_id for v in app_data.variants if v.variant_id != top_one)

    paths = export_bundle(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id=other_variant,
        out_dir=tmp_path,
    )

    assert Path(paths["plan"]).exists()

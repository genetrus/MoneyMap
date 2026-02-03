from __future__ import annotations

from pathlib import Path
from shutil import copytree

import pytest

from money_map.app.api import (
    ValidationFatalsError,
    export_bundle,
    plan_variant,
    recommend_variants,
)
from money_map.storage.fs import read_yaml, write_yaml


def _prepare_invalid_rulepack(tmp_path: Path) -> tuple[Path, str]:
    root = Path(__file__).resolve().parents[1]
    data_dir = tmp_path / "data"
    copytree(root / "data", data_dir)
    rulepack_path = data_dir / "rulepacks" / "DE.yaml"
    rulepack_payload = read_yaml(rulepack_path)
    rulepack_payload["reviewed_at"] = "not-a-date"
    write_yaml(rulepack_path, rulepack_payload)
    variants_payload = read_yaml(data_dir / "variants.yaml")
    variant_id = variants_payload["variants"][0]["variant_id"]
    return data_dir, variant_id


@pytest.mark.parametrize("action", ["recommend", "plan", "export"])
def test_api_blocks_actions_on_validation_fatals(tmp_path: Path, action: str) -> None:
    data_dir, variant_id = _prepare_invalid_rulepack(tmp_path)
    profile_path = Path(__file__).resolve().parents[1] / "profiles" / "demo_fast_start.yaml"

    with pytest.raises(ValidationFatalsError) as excinfo:
        if action == "recommend":
            recommend_variants(profile_path, data_dir=data_dir)
        elif action == "plan":
            plan_variant(profile_path, variant_id, data_dir=data_dir)
        else:
            export_bundle(
                profile_path,
                variant_id,
                out_dir=tmp_path / "exports",
                data_dir=data_dir,
            )

    assert "RULEPACK_REVIEWED_AT_INVALID" in excinfo.value.fatals

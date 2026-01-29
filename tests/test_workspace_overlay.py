from pathlib import Path

from money_map.core.load import load_app_data, load_yaml
from money_map.core.workspace import get_workspace_paths, init_workspace
from money_map.core.yaml_utils import dump_yaml


def test_workspace_overlay_replaces_variant(tmp_path: Path) -> None:
    data_dir = Path("data")
    workspace = tmp_path / "workspace"
    init_workspace(workspace)
    variants = load_yaml(data_dir / "variants.yaml")
    assert isinstance(variants, list)
    base = variants[0]
    modified = dict(base)
    modified["summary_key"] = "variant.overlay.summary"

    overlay_path = get_workspace_paths(workspace).overlay / "variants.yaml"
    overlay_path.write_text(dump_yaml([modified]), encoding="utf-8")

    appdata = load_app_data(data_dir, workspace=workspace)
    updated = next(
        item for item in appdata.variants if item.variant_id == modified["variant_id"]
    )
    assert updated.summary_key == "variant.overlay.summary"

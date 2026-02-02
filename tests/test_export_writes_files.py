from pathlib import Path

from money_map.app.api import export_bundle


def test_export_writes_files(tmp_path: Path):
    paths = export_bundle(
        profile_path="profiles/demo_fast_start.yaml",
        variant_id="de.fast.freelance_writer",
        out_dir=tmp_path,
    )

    assert Path(paths["plan"]).exists()
    assert Path(paths["result"]).exists()
    assert Path(paths["profile"]).exists()

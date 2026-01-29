import tempfile
import unittest
from pathlib import Path

from money_map.app.cli import export_command


class TestExportSnapshots(unittest.TestCase):
    def test_export_snapshots(self) -> None:
        snapshot_dir = Path("tests/snapshots")
        with tempfile.TemporaryDirectory() as temp_dir:
            out_en = Path(temp_dir) / "exports_en"
            out_de = Path(temp_dir) / "exports_de"
            export_command(
                Path("profiles/demo_fast_start.yaml"),
                out_en,
                Path("data"),
                "en",
                "2026-01-01",
            )
            export_command(
                Path("profiles/demo_fast_start.yaml"),
                out_de,
                Path("data"),
                "de",
                "2026-01-01",
            )

            plan_en = out_en / "plan.md"
            plan_de = out_de / "plan.md"
            checklist = out_en / "checklist.md"
            result_json = out_en / "result.json"

            self.assertEqual(
                plan_en.read_text(encoding="utf-8"),
                (snapshot_dir / "plan_en.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                plan_de.read_text(encoding="utf-8"),
                (snapshot_dir / "plan_de.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                checklist.read_text(encoding="utf-8"),
                (snapshot_dir / "checklist.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                result_json.read_text(encoding="utf-8"),
                (snapshot_dir / "result.json").read_text(encoding="utf-8"),
            )

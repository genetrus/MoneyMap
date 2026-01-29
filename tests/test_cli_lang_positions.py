import tempfile
import unittest
from pathlib import Path

try:
    from typer.testing import CliRunner
except ImportError:  # pragma: no cover - optional dependency
    CliRunner = None

from money_map.app.cli import app


class TestCliLangPositions(unittest.TestCase):
    def setUp(self) -> None:
        if app is None or CliRunner is None:
            self.skipTest("Typer is not available")
        self.runner = CliRunner()

    def test_recommend_lang_after_subcommand(self) -> None:
        result = self.runner.invoke(
            app,
            [
                "recommend",
                "--profile",
                "profiles/demo_fast_start.yaml",
                "--top",
                "5",
                "--lang",
                "en",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    def test_export_lang_after_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "exports"
            result = self.runner.invoke(
                app,
                [
                    "export",
                    "--profile",
                    "profiles/demo_fast_start.yaml",
                    "--out",
                    str(out_path),
                    "--lang",
                    "en",
                ],
            )
        self.assertEqual(result.exit_code, 0)

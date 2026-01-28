import subprocess
import sys
import unittest


class TestCliHelp(unittest.TestCase):
    def test_cli_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "money_map", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("validate", result.stdout.lower())

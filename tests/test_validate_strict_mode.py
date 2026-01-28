import unittest
from pathlib import Path

from money_map.core.validate import validate_app_data


class TestValidateStrictMode(unittest.TestCase):
    def test_validate_strict_mode(self) -> None:
        fatals, _ = validate_app_data(Path("data"), strict=True)
        self.assertEqual(fatals, [])

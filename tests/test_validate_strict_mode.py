import unittest
from pathlib import Path

from money_map.core.load import load_app_data
from money_map.core.model import EconomicsSnapshot
from money_map.core.validate import validate_app_data


class TestValidateStrictMode(unittest.TestCase):
    def test_validate_strict_mode(self) -> None:
        fatals, _ = validate_app_data(Path("data"), strict=True)
        self.assertEqual(fatals, [])

    def test_variant_economics_typed(self) -> None:
        appdata = load_app_data(Path("data"))
        econ = appdata.variants[0].economics
        self.assertIsInstance(econ, (EconomicsSnapshot, type(None)))

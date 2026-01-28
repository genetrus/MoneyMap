import unittest
from pathlib import Path

from money_map.core.validate import validate_app_data


class TestValidateSeedData(unittest.TestCase):
    def test_validate_seed_data(self) -> None:
        fatals, _ = validate_app_data(Path("data"))
        self.assertEqual(fatals, [])

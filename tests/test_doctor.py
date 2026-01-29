import unittest
from pathlib import Path

from money_map.app.cli import doctor_command


class TestDoctor(unittest.TestCase):
    def test_doctor_command(self) -> None:
        result = doctor_command(Path("data"), "en")
        self.assertEqual(result, 0)

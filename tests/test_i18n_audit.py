import unittest
from pathlib import Path

from money_map.i18n.audit import audit_i18n


class TestI18NAudit(unittest.TestCase):
    def test_i18n_audit_core_keys(self) -> None:
        fatals, _ = audit_i18n(Path("data"))
        self.assertEqual(fatals, [])

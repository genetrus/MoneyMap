import importlib
import unittest


class TestSmokeImports(unittest.TestCase):
    def test_imports(self) -> None:
        importlib.import_module("money_map.app.cli")
        importlib.import_module("money_map.core.load")
        importlib.import_module("money_map.core.validate")
        importlib.import_module("money_map.i18n.i18n")

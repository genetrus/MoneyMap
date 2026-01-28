import importlib


def test_imports() -> None:
    importlib.import_module("money_map.app.cli")
    importlib.import_module("money_map.core.load")
    importlib.import_module("money_map.i18n.i18n")
    importlib.import_module("money_map.ui")

import importlib


def test_imports() -> None:
    importlib.import_module("money_map.app.cli")
    importlib.import_module("money_map.ui.app")
    importlib.import_module("money_map.core.load")

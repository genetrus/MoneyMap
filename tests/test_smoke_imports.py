import importlib.util


def test_smoke_imports():
    import money_map

    assert money_map.__name__ == "money_map"

    if importlib.util.find_spec("money_map.ui") is not None:
        import money_map.ui

        assert money_map.ui.__name__ == "money_map.ui"

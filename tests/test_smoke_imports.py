import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def test_smoke_imports():
    import money_map

    assert money_map.__name__ == "money_map"

    if importlib.util.find_spec("money_map.ui") is not None:
        import money_map.ui
        assert money_map.ui.__name__ == "money_map.ui"

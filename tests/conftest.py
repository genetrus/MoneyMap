from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
try:
    import money_map  # noqa: F401
except ModuleNotFoundError:
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))

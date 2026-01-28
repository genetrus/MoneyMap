from __future__ import annotations

import pkgutil
from pathlib import Path

__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore[name-defined]

SRC = Path(__file__).resolve().parent.parent / "src" / "money_map"
if SRC.exists():
    __path__.append(str(SRC))

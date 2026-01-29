from __future__ import annotations

from money_map.app.cli import app, main

if __name__ == "__main__":
    if app is not None:
        app(prog_name="money_map")
    else:
        raise SystemExit(main())

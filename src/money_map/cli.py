"""Backward-compatible CLI shim."""

from money_map.app.cli import app, main

__all__ = ["app", "main"]


if __name__ == "__main__":
    main()

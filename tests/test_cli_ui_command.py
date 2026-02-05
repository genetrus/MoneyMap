from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from money_map.app import cli


class _BoolSequence:
    def __init__(self, values: list[bool]) -> None:
        self._values = values
        self._index = 0

    def __call__(self) -> bool:
        if self._index >= len(self._values):
            return self._values[-1]
        value = self._values[self._index]
        self._index += 1
        return value


def test_ui_missing_streamlit_prints_install_guidance(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_streamlit_installed", lambda: False)

    with pytest.raises(cli.typer.Exit) as exc_info:
        cli.ui()

    assert exc_info.value.exit_code == 1
    output = capsys.readouterr().out
    assert 'python -m pip install -e ".[ui]"' in output
    assert "python scripts/install_ui_deps.py" in output


def test_ui_install_flag_bootstraps_and_launches(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_streamlit_installed", _BoolSequence([False, True]))
    calls: list[list[str]] = []

    def _fake_run(cmd, **_kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.subprocess, "run", _fake_run)

    cli.ui(install=True)

    install_script = Path(str(calls[0][-1]))
    assert install_script.name == "install_ui_deps.py"
    assert install_script.parent.name == "scripts"
    assert calls[1][1:4] == ["-m", "streamlit", "run"]

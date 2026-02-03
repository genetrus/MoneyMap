import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def test_smoke_imports():
    import money_map

    assert money_map.__name__ == "money_map"

    if importlib.util.find_spec("money_map.ui") is not None:
        import money_map.ui

        assert money_map.ui.__name__ == "money_map.ui"


def test_cli_validate_smoke():
    env = dict(**os.environ)
    repo_src = Path(__file__).resolve().parents[1] / "src"
    try:
        import money_map
    except ModuleNotFoundError:
        env["PYTHONPATH"] = str(repo_src)
    else:
        if Path(money_map.__file__ or "").resolve().is_relative_to(repo_src):
            env["PYTHONPATH"] = str(repo_src)
    result = subprocess.run(
        [sys.executable, "-m", "money_map.app.cli", "validate", "--data-dir", "data"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr

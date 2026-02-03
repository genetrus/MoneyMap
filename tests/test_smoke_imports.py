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
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "validation report" in combined.lower(), combined


def test_console_script_validate_smoke():
    script_name = "money-map.exe" if os.name == "nt" else "money-map"
    cli_path = Path(sys.executable).parent / script_name
    assert cli_path.exists(), (
        f"Expected console script at {cli_path}. Ensure the package is installed in the "
        "test environment."
    )
    result = subprocess.run(
        [str(cli_path), "validate", "--data-dir", "data"],
        check=False,
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "validation report" in combined.lower(), combined

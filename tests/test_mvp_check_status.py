from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_mvp_check_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "mvp_check.py"
    spec = importlib.util.spec_from_file_location("mvp_check", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_mvp_check_all_pass():
    module = _load_mvp_check_module()
    results = [module.CheckResult(name="one", status="PASS", detail="ok")]
    status, exit_code, failures, skips = module._summarize_results(results)
    assert (status, exit_code, failures, skips) == ("MVP PASSED", 0, 0, 0)


def test_mvp_check_incomplete():
    module = _load_mvp_check_module()
    results = [module.CheckResult(name="ui", status="SKIP", detail="missing")]
    status, exit_code, failures, skips = module._summarize_results(results)
    assert (status, exit_code, failures, skips) == ("MVP INCOMPLETE", 2, 0, 1)


def test_mvp_check_failed():
    module = _load_mvp_check_module()
    results = [module.CheckResult(name="bad", status="FAIL", detail="boom")]
    status, exit_code, failures, skips = module._summarize_results(results)
    assert (status, exit_code, failures, skips) == ("MVP FAILED", 1, 1, 0)

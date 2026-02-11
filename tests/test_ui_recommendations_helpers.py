import importlib.util

import pytest


class _Feas:
    def __init__(self, status: str):
        self.status = status


class _Econ:
    def __init__(self):
        self.time_to_first_money_days_range = [10, 20]
        self.typical_net_month_eur_range = [1000, 1500]
        self.confidence = "medium"


class _Legal:
    def __init__(self, gate: str):
        self.legal_gate = gate


class _Rec:
    def __init__(self):
        self.feasibility = _Feas("feasible")
        self.economics = _Econ()
        self.legal = _Legal("ok")


def test_score_contribution_rows_shape() -> None:
    if importlib.util.find_spec("streamlit") is None:
        pytest.skip("streamlit not installed in test environment")

    from money_map.ui.app import _score_contribution_rows

    rows = _score_contribution_rows(_Rec())
    factors = {row["factor"] for row in rows}
    assert factors == {"feasibility", "legal", "speed", "net", "confidence"}
    assert all(0 <= float(row["value"]) <= 100 for row in rows)

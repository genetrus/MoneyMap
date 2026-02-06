"""Economics estimations."""

from __future__ import annotations

from money_map.core.model import EconomicsResult, Variant

ALLOWED_CONFIDENCE = {"low", "medium", "high", "unknown"}


def _normalize_range(value: object, default: list[int]) -> list[int]:
    if not isinstance(value, list) or len(value) != 2:
        return default
    left, right = value[0], value[1]
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return default
    left_i = int(left)
    right_i = int(right)
    if left_i > right_i:
        return [right_i, left_i]
    return [left_i, right_i]


def assess_economics(variant: Variant) -> EconomicsResult:
    economics = variant.economics or {}

    first_money = _normalize_range(economics.get("time_to_first_money_days_range"), [0, 0])
    net_month = _normalize_range(economics.get("typical_net_month_eur_range"), [0, 0])
    costs = _normalize_range(economics.get("costs_eur_range"), [0, 0])

    volatility = economics.get("volatility_or_seasonality") or economics.get("volatility")
    confidence = str(economics.get("confidence", "unknown")).lower()
    if confidence not in ALLOWED_CONFIDENCE:
        confidence = "unknown"

    return EconomicsResult(
        time_to_first_money_days_range=first_money,
        typical_net_month_eur_range=net_month,
        costs_eur_range=costs,
        volatility_or_seasonality=volatility or "unknown",
        variable_costs=economics.get("variable_costs") or "unknown",
        scaling_ceiling=economics.get("scaling_ceiling") or "unknown",
        confidence=confidence,
    )

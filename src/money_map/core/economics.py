"""Economics estimations."""

from __future__ import annotations

from money_map.core.model import EconomicsResult, Variant


def assess_economics(variant: Variant) -> EconomicsResult:
    economics = variant.economics
    return EconomicsResult(
        time_to_first_money_days_range=list(economics.get("time_to_first_money_days_range", [0, 0])),
        typical_net_month_eur_range=list(economics.get("typical_net_month_eur_range", [0, 0])),
        costs_eur_range=list(economics.get("costs_eur_range", [0, 0])),
        volatility_or_seasonality=economics.get("volatility_or_seasonality") or "unknown",
        variable_costs=economics.get("variable_costs") or "unknown",
        scaling_ceiling=economics.get("scaling_ceiling") or "unknown",
        confidence=str(economics.get("confidence", "unknown")),
    )

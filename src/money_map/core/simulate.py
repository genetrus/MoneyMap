from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import json
from typing import Any

from money_map.core.model import EconomicsSnapshot, ObjectivePreset, UserProfile, Variant
from money_map.i18n import t
from money_map.i18n.locale import format_currency


@dataclass
class MonthRow:
    month_index: int
    month_label: str
    revenue: float
    opex: float
    capex: float
    net: float
    cum_net: float
    hours_required: float
    feasibility_flags: list[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    months: list[MonthRow]
    assumptions: list[str]
    risks: list[str]
    breakeven_month: int | None


def _month_label(today: date, month_index: int) -> str:
    year = today.year + (today.month - 1 + (month_index - 1)) // 12
    month = ((today.month - 1 + (month_index - 1)) % 12) + 1
    return f"{year:04d}-{month:02d}"


def _cap_revenue(revenue: float, hours: int) -> tuple[float, list[str]]:
    if hours <= 0:
        return 0.0, ["sim.assumption.zero_hours"]
    cap_ratio = min(1.0, hours / 40)
    if cap_ratio < 1.0:
        return revenue * cap_ratio, ["sim.assumption.time_cap"]
    return revenue, []


def simulate_variant(
    profile: UserProfile,
    variant: Variant,
    preset: ObjectivePreset | None,
    horizon_months: int,
    today: date,
    overrides: dict[str, Any] | None = None,
) -> SimulationResult:
    overrides = overrides or {}
    econ: EconomicsSnapshot = variant.economics or EconomicsSnapshot()
    time_to_first = variant.feasibility.time_to_first_eur_days if variant.feasibility else None
    opex = econ.opex_monthly_eur or 0
    capex = econ.capex_eur or 0
    low = econ.expected_net_monthly_eur_low or 0
    high = econ.expected_net_monthly_eur_high
    assumptions: list[str] = []
    if econ.expected_net_monthly_eur_low is None:
        assumptions.append("sim.assumption.missing_revenue_low")
    midpoint = (low + high) / 2 if high is not None else low

    offset_months = 0
    if time_to_first and time_to_first > 30:
        offset_months = max(1, int((time_to_first + 29) // 30)) - 1
        assumptions.append("sim.assumption.delayed_start")

    months: list[MonthRow] = []
    cum_net = 0.0
    breakeven_month = None
    for month_index in range(1, horizon_months + 1):
        base_revenue = 0.0
        if month_index > offset_months:
            ramp_index = month_index - offset_months
            if ramp_index <= 2:
                base_revenue = low * (ramp_index / 2)
            elif ramp_index <= 4:
                step = (midpoint - low) / 2 if midpoint != low else 0
                base_revenue = low + step * (ramp_index - 2)
            else:
                base_revenue = midpoint
        revenue, flags = _cap_revenue(base_revenue, profile.time_hours_per_week)
        month_capex = capex if month_index == 1 else 0
        month_net = revenue - opex - month_capex
        cum_net += month_net
        if breakeven_month is None and cum_net >= 0:
            breakeven_month = month_index
        months.append(
            MonthRow(
                month_index=month_index,
                month_label=_month_label(today, month_index),
                revenue=round(revenue, 2),
                opex=round(opex, 2),
                capex=round(month_capex, 2),
                net=round(month_net, 2),
                cum_net=round(cum_net, 2),
                hours_required=float(profile.time_hours_per_week),
                feasibility_flags=flags,
            )
        )

    return SimulationResult(
        months=months,
        assumptions=assumptions,
        risks=[],
        breakeven_month=breakeven_month,
    )


def simulation_to_json(result: SimulationResult) -> dict[str, Any]:
    return {
        "months": [
            {
                "month_index": item.month_index,
                "month_label": item.month_label,
                "revenue": item.revenue,
                "opex": item.opex,
                "capex": item.capex,
                "net": item.net,
                "cum_net": item.cum_net,
                "hours_required": item.hours_required,
                "feasibility_flags": item.feasibility_flags,
            }
            for item in result.months
        ],
        "assumptions": result.assumptions,
        "risks": result.risks,
        "breakeven_month": result.breakeven_month,
    }


def simulation_to_json_text(result: SimulationResult) -> str:
    return json.dumps(simulation_to_json(result), indent=2, sort_keys=True)


def simulation_to_markdown(result: SimulationResult, lang: str) -> str:
    headers = [
        t("sim.table.month", lang),
        t("sim.table.revenue", lang),
        t("sim.table.opex", lang),
        t("sim.table.capex", lang),
        t("sim.table.net", lang),
        t("sim.table.cum_net", lang),
    ]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join([" --- "] * len(headers)) + "|"]
    for row in result.months:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.month_label,
                    format_currency(row.revenue, lang),
                    format_currency(row.opex, lang),
                    format_currency(row.capex, lang),
                    format_currency(row.net, lang),
                    format_currency(row.cum_net, lang),
                ]
            )
            + " |"
        )
    lines.append("")
    if result.breakeven_month:
        lines.append(
            f"{t('sim.breakeven', lang)}: {result.breakeven_month}"
        )
    if result.assumptions:
        lines.append(f"{t('sim.assumptions', lang)}: " + ", ".join(result.assumptions))
    return "\n".join(lines).strip() + "\n"

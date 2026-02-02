"""Recommendation engine."""

from __future__ import annotations

from money_map.core.economics import assess_economics
from money_map.core.feasibility import assess_feasibility
from money_map.core.model import RecommendationResult, RecommendationVariant, Variant
from money_map.core.rules import evaluate_legal


def _score_variant(variant: Variant, objective: str) -> float:
    economics = variant.economics
    time_range = economics.get("time_to_first_money_days_range", [0, 0])
    net_range = economics.get("typical_net_month_eur_range", [0, 0])
    time_mid = sum(time_range) / 2 if time_range else 0
    net_mid = sum(net_range) / 2 if net_range else 0

    if objective == "max_net":
        return net_mid - time_mid * 0.5
    return (-time_mid) + net_mid * 0.01


def recommend(
    profile: dict,
    variants: list[Variant],
    rulepack,
    objective_preset: str = "fastest_money",
    filters: dict | None = None,
    top_n: int = 5,
) -> RecommendationResult:
    filters = filters or {}
    diagnostics = {"filtered_out": 0, "reasons": {}}

    ranked: list[RecommendationVariant] = []
    for variant in variants:
        feasibility = assess_feasibility(profile, variant)
        economics = assess_economics(variant)
        legal = evaluate_legal(rulepack, variant)

        max_time = filters.get("max_time_to_money_days")
        if max_time and economics.time_to_first_money_days_range[1] > max_time:
            diagnostics["filtered_out"] += 1
            diagnostics["reasons"].setdefault("time_to_money", 0)
            diagnostics["reasons"]["time_to_money"] += 1
            continue
        if filters.get("exclude_blocked") and legal.legal_gate == "blocked":
            diagnostics["filtered_out"] += 1
            diagnostics["reasons"].setdefault("blocked", 0)
            diagnostics["reasons"]["blocked"] += 1
            continue

        score = _score_variant(variant, objective_preset)
        pros = [
            f"Estimated net {economics.typical_net_month_eur_range[0]}–{economics.typical_net_month_eur_range[1]} €/mo",
            f"Time to first money {economics.time_to_first_money_days_range[0]}–{economics.time_to_first_money_days_range[1]} days",
            f"Confidence: {economics.confidence}",
        ]
        cons = []
        if feasibility.blockers:
            cons.append("Prep needed: " + "; ".join(feasibility.blockers[:2]))
        if legal.legal_gate != "ok":
            cons.append(f"Legal gate: {legal.legal_gate}")

        ranked.append(
            RecommendationVariant(
                variant=variant,
                score=score,
                feasibility=feasibility,
                economics=economics,
                legal=legal,
                pros=pros,
                cons=cons[:2],
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.variant.variant_id))
    return RecommendationResult(ranked_variants=ranked[:top_n], diagnostics=diagnostics)

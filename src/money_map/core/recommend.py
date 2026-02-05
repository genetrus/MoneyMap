"""Recommendation engine."""

from __future__ import annotations

from dataclasses import asdict

from money_map.core.economics import assess_economics
from money_map.core.feasibility import assess_feasibility
from money_map.core.model import (
    RecommendationResult,
    RecommendationVariant,
    StalenessPolicy,
    Variant,
)
from money_map.core.profile import profile_hash as compute_profile_hash
from money_map.core.rules import evaluate_legal
from money_map.core.staleness import evaluate_staleness

LEGAL_FRICTION_SCORE = {
    "ok": 0,
    "require_check": 1,
    "registration": 2,
    "license": 3,
    "blocked": 4,
}


def is_variant_stale(variant: Variant, policy: StalenessPolicy) -> bool:
    return evaluate_staleness(variant.review_date, policy, label="variant").is_stale


def _score_variant(variant: Variant, objective: str) -> float:
    economics = variant.economics
    time_range = economics.get("time_to_first_money_days_range", [0, 0])
    net_range = economics.get("typical_net_month_eur_range", [0, 0])
    time_mid = sum(time_range) / 2 if time_range else 0
    net_mid = sum(net_range) / 2 if net_range else 0

    if objective == "max_net":
        return net_mid - time_mid * 0.5
    return (-time_mid) + net_mid * 0.01


def _inc_reason(diagnostics: dict, code: str) -> None:
    diagnostics["filtered_out"] += 1
    diagnostics["reasons"].setdefault(code, 0)
    diagnostics["reasons"][code] += 1


def recommend(
    profile: dict,
    variants: list[Variant],
    rulepack,
    staleness_policy: StalenessPolicy,
    objective_preset: str = "fastest_money",
    filters: dict | None = None,
    top_n: int = 5,
) -> RecommendationResult:
    filters = filters or {}
    diagnostics = {
        "filtered_out": 0,
        "reasons": {},
        "warnings": {},
        "evaluated": len(variants),
        "applied_filters": dict(filters),
    }

    profile_fingerprint = compute_profile_hash(profile)
    ranked: list[RecommendationVariant] = []
    for variant in variants:
        feasibility = assess_feasibility(profile, variant)
        economics = assess_economics(variant)
        legal = evaluate_legal(rulepack, variant, staleness_policy)
        staleness = evaluate_staleness(
            variant.review_date,
            staleness_policy,
            label=f"variant:{variant.variant_id}",
        )
        stale = staleness.is_stale

        if stale:
            diagnostics["warnings"].setdefault("stale_variant", 0)
            diagnostics["warnings"]["stale_variant"] += 1

        max_time = filters.get("max_time_to_first_money_days") or filters.get(
            "max_time_to_money_days"
        )
        if max_time and economics.time_to_first_money_days_range[1] > int(max_time):
            _inc_reason(diagnostics, "time_to_money")
            continue

        min_net = filters.get("min_typical_net_month")
        if min_net and economics.typical_net_month_eur_range[0] < int(min_net):
            _inc_reason(diagnostics, "min_typical_net_month")
            continue

        allowed_gates = filters.get("allowed_legal_gates")
        if allowed_gates and legal.legal_gate not in allowed_gates:
            _inc_reason(diagnostics, "allowed_legal_gates")
            continue

        max_legal_friction = filters.get("max_legal_friction")
        if max_legal_friction is not None and LEGAL_FRICTION_SCORE.get(legal.legal_gate, 99) > int(
            max_legal_friction
        ):
            _inc_reason(diagnostics, "max_legal_friction")
            continue

        if filters.get("exclude_blocked") and legal.legal_gate == "blocked":
            _inc_reason(diagnostics, "blocked")
            continue

        if (
            filters.get("compliance_mode") == "exclude_if_requires_prep"
            and legal.legal_gate != "ok"
        ):
            _inc_reason(diagnostics, "compliance_mode")
            continue

        allowed_feasibility = filters.get("allowed_feasibility_status")
        if allowed_feasibility and feasibility.status not in allowed_feasibility:
            _inc_reason(diagnostics, "allowed_feasibility_status")
            continue

        include_tags = set(filters.get("include_tags") or [])
        if include_tags and not include_tags.intersection(set(variant.tags)):
            _inc_reason(diagnostics, "include_tags")
            continue

        exclude_tags = set(filters.get("exclude_tags") or [])
        if exclude_tags and exclude_tags.intersection(set(variant.tags)):
            _inc_reason(diagnostics, "exclude_tags")
            continue

        score = _score_variant(variant, objective_preset)
        if not variant.economics:
            score -= 50
            diagnostics["warnings"].setdefault("missing_economics", 0)
            diagnostics["warnings"]["missing_economics"] += 1
        pros = [
            "Estimated net "
            f"{economics.typical_net_month_eur_range[0]}–"
            f"{economics.typical_net_month_eur_range[1]} €/mo",
            "Time to first money "
            f"{economics.time_to_first_money_days_range[0]}–"
            f"{economics.time_to_first_money_days_range[1]} days",
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
                stale=stale,
                staleness=asdict(staleness),
                pros=pros,
                cons=cons[:2],
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.variant.variant_id))
    return RecommendationResult(
        ranked_variants=ranked[:top_n],
        diagnostics=diagnostics,
        profile_hash=profile_fingerprint,
    )

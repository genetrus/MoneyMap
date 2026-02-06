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


def is_variant_stale(variant: Variant, policy: StalenessPolicy) -> bool:
    return evaluate_staleness(variant.review_date, policy, label="variant").is_stale


def _objective_weights(objective: str) -> dict[str, float]:
    if objective == "max_net":
        return {
            "time": 0.4,
            "net": 1.2,
            "legal": 0.7,
            "feasibility": 0.8,
            "prep": 0.5,
            "confidence": 0.4,
        }
    if objective == "balanced":
        return {
            "time": 0.9,
            "net": 0.9,
            "legal": 0.9,
            "feasibility": 0.9,
            "prep": 0.9,
            "confidence": 0.6,
        }
    # fastest_money default
    return {
        "time": 1.2,
        "net": 0.35,
        "legal": 0.8,
        "feasibility": 1.0,
        "prep": 0.9,
        "confidence": 0.4,
    }


def _score_variant(feasibility, economics, legal, objective: str) -> float:
    weights = _objective_weights(objective)

    time_min, time_max = economics.time_to_first_money_days_range
    net_min, net_max = economics.typical_net_month_eur_range
    prep_min, prep_max = feasibility.estimated_prep_weeks_range

    time_mid = (time_min + time_max) / 2
    net_mid = (net_min + net_max) / 2
    prep_mid = (prep_min + prep_max) / 2

    legal_score_map = {
        "ok": 1.0,
        "require_check": 0.4,
        "registration": 0.2,
        "license": 0.1,
        "blocked": -1.0,
    }
    feasibility_score_map = {
        "feasible": 1.0,
        "feasible_with_prep": 0.4,
        "not_feasible": -0.8,
    }
    confidence_score_map = {
        "low": 0.2,
        "medium": 0.6,
        "high": 1.0,
        "unknown": 0.4,
    }

    legal_score = legal_score_map.get(legal.legal_gate, 0.0)
    feasibility_score = feasibility_score_map.get(feasibility.status, 0.0)
    confidence_score = confidence_score_map.get(economics.confidence, 0.4)

    return (
        weights["time"] * (-time_mid)
        + weights["net"] * (net_mid / 100)
        + weights["legal"] * legal_score
        + weights["feasibility"] * feasibility_score
        + weights["prep"] * (-prep_mid)
        + weights["confidence"] * confidence_score
    )


def _normalized_constraints(profile: dict) -> set[str]:
    raw = profile.get("constraints", [])
    if not isinstance(raw, list):
        return set()
    return {str(item).strip().lower() for item in raw if str(item).strip()}


def _is_regulated_excluded(constraints: set[str], variant: Variant) -> bool:
    if not constraints:
        return False
    regulated_markers = {
        "без лицензируемых сфер",
        "no_regulated",
        "no_regulated_domains",
        "no_license",
    }
    if constraints.isdisjoint(regulated_markers):
        return False
    tags = {str(tag).strip().lower() for tag in variant.tags}
    gate = str((variant.legal or {}).get("legal_gate", "")).lower()
    return "regulated" in tags or gate in {"registration", "license", "blocked"}


def _candidate_filter_reason(profile: dict, variant: Variant) -> str | None:
    constraints = _normalized_constraints(profile)
    if _is_regulated_excluded(constraints, variant):
        return "constraint_regulated"

    required_assets = set((variant.feasibility or {}).get("required_assets", []))
    available_assets = (
        set(profile.get("assets", [])) if isinstance(profile.get("assets"), list) else set()
    )
    if required_assets and not available_assets:
        return "missing_assets_all"
    return None


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
        "candidates": 0,
    }

    profile_fingerprint = compute_profile_hash(profile)

    candidate_variants: list[Variant] = []
    for variant in variants:
        reason = _candidate_filter_reason(profile, variant)
        if reason:
            diagnostics["filtered_out"] += 1
            diagnostics["reasons"].setdefault(reason, 0)
            diagnostics["reasons"][reason] += 1
            continue
        candidate_variants.append(variant)

    diagnostics["candidates"] = len(candidate_variants)

    ranked: list[RecommendationVariant] = []
    for variant in candidate_variants:
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
        if filters.get("exclude_not_feasible") and feasibility.status == "not_feasible":
            diagnostics["filtered_out"] += 1
            diagnostics["reasons"].setdefault("not_feasible", 0)
            diagnostics["reasons"]["not_feasible"] += 1
            continue

        score = _score_variant(feasibility, economics, legal, objective_preset)
        if not variant.economics:
            score -= 50
            diagnostics["warnings"].setdefault("missing_economics", 0)
            diagnostics["warnings"]["missing_economics"] += 1

        if economics.time_to_first_money_days_range == [0, 0]:
            diagnostics["warnings"].setdefault("economics_first_money_unknown", 0)
            diagnostics["warnings"]["economics_first_money_unknown"] += 1
        if economics.typical_net_month_eur_range == [0, 0]:
            diagnostics["warnings"].setdefault("economics_net_unknown", 0)
            diagnostics["warnings"]["economics_net_unknown"] += 1
        if economics.costs_eur_range == [0, 0]:
            diagnostics["warnings"].setdefault("economics_costs_unknown", 0)
            diagnostics["warnings"]["economics_costs_unknown"] += 1
        if feasibility.status == "not_feasible":
            score -= 75
            diagnostics["warnings"].setdefault("not_feasible_penalized", 0)
            diagnostics["warnings"]["not_feasible_penalized"] += 1

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
        if feasibility.status == "not_feasible":
            cons.append("Not feasible now: requires major prep")
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

    # Deterministic ordering: score desc, then variant_id asc for tie-breaks.
    ranked.sort(key=lambda item: (-item.score, item.variant.variant_id))
    return RecommendationResult(
        ranked_variants=ranked[:top_n],
        diagnostics=diagnostics,
        profile_hash=profile_fingerprint,
    )

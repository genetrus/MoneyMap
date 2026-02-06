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


def _score_variant(variant: Variant, objective: str) -> float:
    economics = variant.economics
    time_range = economics.get("time_to_first_money_days_range", [0, 0])
    net_range = economics.get("typical_net_month_eur_range", [0, 0])
    time_mid = sum(time_range) / 2 if time_range else 0
    net_mid = sum(net_range) / 2 if net_range else 0

    if objective == "max_net":
        return net_mid - time_mid * 0.5
    return (-time_mid) + net_mid * 0.01


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

        score = _score_variant(variant, objective_preset)
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

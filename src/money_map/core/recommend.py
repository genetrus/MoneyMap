from __future__ import annotations

from datetime import date, datetime

from money_map.core.load import AppData
from money_map.core.evidence import EvidenceRegistry
from money_map.core.model import (
    ObjectivePreset,
    RankedVariant,
    RecommendationResult,
    UserProfile,
    Variant,
)
from money_map.core.reviews import normalize_review_date, review_status_for_entity, ReviewsIndex
from money_map.core.rules import evaluate_rulepack


def _to_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.today()


def _clamp(value: float, min_value: float = 0, max_value: float = 100) -> float:
    return max(min_value, min(max_value, value))


def _review_date(variant: Variant) -> date:
    if variant.evidence and variant.evidence.last_verified_at:
        return _to_date(variant.evidence.last_verified_at)
    return _to_date(variant.review_date)


def _constraint_conflicts(profile: UserProfile, variant: Variant) -> list[str]:
    conflicts: list[str] = []
    constraint_terms = {item.lower() for item in profile.constraints}
    tag_terms = {item.lower() for item in variant.tags}
    variant_constraints = {item.lower() for item in variant.constraints}
    for term in constraint_terms:
        if term in tag_terms or term in variant_constraints:
            conflicts.append(term)
    if "no_customer_facing" in constraint_terms and "community" in tag_terms:
        conflicts.append("no_customer_facing")
    if "no_driving" in constraint_terms and "delivery" in tag_terms:
        conflicts.append("no_driving")
    return conflicts


def _assumptions_for_variant(variant: Variant) -> list[str]:
    assumptions: list[str] = []
    tags = set(variant.tags)
    if "remote" in tags:
        assumptions.append("assumption.platform_access")
    if "inventory" in tags:
        assumptions.append("assumption.supplier_reliability")
    if "community" in tags:
        assumptions.append("assumption.community_engagement")
    if "content" in tags:
        assumptions.append("assumption.content_quality")
    if "automation" in tags:
        assumptions.append("assumption.client_data_access")
    assumptions.append("assumption.market_demand")
    assumptions.append("assumption.client_acquisition")
    return assumptions


def _scoring_weights(preset: ObjectivePreset | None = None) -> dict[str, float]:
    if preset is None:
        return {
            "feasibility": 0.25,
            "economics": 0.25,
            "legal": 0.2,
            "fit": 0.2,
            "staleness": 0.1,
        }
    return {
        "feasibility": preset.weight_feasibility,
        "economics": preset.weight_economics,
        "legal": preset.weight_legal,
        "fit": preset.weight_fit,
        "staleness": preset.weight_staleness,
    }


def _find_preset(profile: UserProfile, appdata: AppData) -> ObjectivePreset | None:
    for preset in appdata.presets:
        if preset.preset_id == profile.objective_preset:
            return preset
    return appdata.presets[0] if appdata.presets else None


def recommend(
    profile: UserProfile,
    appdata: AppData,
    top_n: int,
    today: date | None = None,
    reviews: ReviewsIndex | None = None,
    evidence_registry: EvidenceRegistry | None = None,
) -> RecommendationResult:
    policy = appdata.meta.staleness_policy
    today = today or date.today()
    meta_days = (today - _to_date(appdata.meta.reviewed_at)).days
    rulepack_days = (today - _to_date(appdata.rulepack.reviewed_at)).days
    regulated_tags = set(policy.regulated_tags)
    preset = _find_preset(profile, appdata)
    if preset and preset.constraints_profile_overrides is not None:
        profile = UserProfile.model_validate(
            {
                **(profile.model_dump() if hasattr(profile, "model_dump") else profile.__dict__),
                "constraints": preset.constraints_profile_overrides,
            }
        )

    evidence_ids = (
        {item.evidence_id for item in evidence_registry.items}
        if evidence_registry is not None
        else set()
    )
    ranked: list[RankedVariant] = []
    for variant in sorted(appdata.variants, key=lambda item: item.variant_id):
        rule_eval = evaluate_rulepack(profile, variant, appdata.rulepack, today=today)
        review_date = _review_date(variant)
        days_since_review = (today - review_date).days
        is_regulated = bool(regulated_tags.intersection(variant.tags)) or (
            variant.legal.regulated_level != "none"
        )
        is_stale_warn = days_since_review > policy.warn_after_days
        is_stale_force = days_since_review > policy.force_require_check_after_days
        review_entry = review_status_for_entity(reviews, f"variant:{variant.variant_id}")
        review_verified_at = normalize_review_date(
            review_entry.verified_at if review_entry else None
        )

        prerequisites = set(variant.feasibility.prerequisites)
        available = set(profile.skills + profile.assets)
        missing_prereqs = sorted(item for item in prerequisites if item not in available)

        complexity = variant.feasibility.complexity
        time_to_first = variant.feasibility.time_to_first_eur_days
        horizon_days = profile.horizon_months * 30

        feasibility_score = 100 - (complexity - 1) * 12
        feasibility_score -= 8 * len(missing_prereqs)
        if time_to_first and time_to_first > horizon_days:
            feasibility_score -= 15
        if profile.time_hours_per_week < 10 and complexity >= 4:
            feasibility_score -= 10
        feasibility_score = _clamp(feasibility_score)

        economics_score = 80
        if variant.economics.capex_eur is not None:
            if variant.economics.capex_eur > profile.capital_eur:
                economics_score -= 25
            else:
                economics_score += 5
        if profile.target_net_monthly_eur and variant.economics.expected_net_monthly_eur_high:
            if variant.economics.expected_net_monthly_eur_high >= profile.target_net_monthly_eur:
                economics_score += 10
            else:
                economics_score -= 15
        if time_to_first and time_to_first > horizon_days:
            economics_score -= 10
        if (
            variant.economics.opex_monthly_eur
            and variant.economics.expected_net_monthly_eur_low
            and variant.economics.opex_monthly_eur > variant.economics.expected_net_monthly_eur_low
        ):
            economics_score -= 10
        economics_score = _clamp(economics_score)

        regulated_level = variant.legal.regulated_level
        legal_score = {"none": 100, "light": 85, "medium": 70, "high": 55}.get(
            regulated_level, 70
        )
        legal_score -= min(15, len(rule_eval.required_kits) * 3)
        if is_regulated and is_stale_force:
            legal_score -= 25
        if "reason.legal.placeholder_rulepack" in rule_eval.blockers:
            legal_score -= 30
        legal_score = _clamp(legal_score)

        fit_score = 70
        if profile.preferred_modes and (
            variant.feasibility.operational_mode in profile.preferred_modes
        ):
            fit_score += 15
        conflicts = _constraint_conflicts(profile, variant)
        if conflicts:
            fit_score -= 10 * len(conflicts)
        fit_score = _clamp(fit_score)

        staleness_score = 100
        if is_stale_warn:
            staleness_score = 80
        if is_stale_force:
            staleness_score = 50
        if is_regulated and is_stale_force:
            staleness_score = 30
        staleness_score = _clamp(staleness_score)

        weights = _scoring_weights(preset)
        score_breakdown = {
            "feasibility": feasibility_score,
            "economics": economics_score,
            "legal": legal_score,
            "fit": fit_score,
            "staleness": staleness_score,
        }
        score_total = sum(score_breakdown[key] * weights[key] for key in weights)

        pros: list[str] = []
        cons: list[str] = []
        blockers: list[str] = []

        if complexity <= 2:
            pros.append("reason.feasibility.low_complexity")
        if not missing_prereqs:
            pros.append("reason.feasibility.prerequisites_met")
        if time_to_first and time_to_first <= 30:
            pros.append("reason.feasibility.fast_time_to_first")
        if (
            variant.economics.capex_eur is not None
            and variant.economics.capex_eur <= profile.capital_eur
        ):
            pros.append("reason.economics.capex_within")
        if (
            profile.target_net_monthly_eur
            and variant.economics.expected_net_monthly_eur_high
            and variant.economics.expected_net_monthly_eur_high >= profile.target_net_monthly_eur
        ):
            pros.append("reason.economics.meets_target")
        if regulated_level == "none":
            pros.append("reason.legal.unregulated")
        if profile.preferred_modes and (
            variant.feasibility.operational_mode in profile.preferred_modes
        ):
            pros.append("reason.fit.preferred_mode")

        if complexity >= 4:
            cons.append("reason.feasibility.high_complexity")
        if missing_prereqs:
            cons.append("reason.feasibility.missing_prerequisite")
        if time_to_first and time_to_first > horizon_days:
            cons.append("reason.feasibility.slow_time_to_first")
        if (
            variant.economics.capex_eur is not None
            and variant.economics.capex_eur > profile.capital_eur
        ):
            cons.append("reason.economics.capex_high")
        if (
            profile.target_net_monthly_eur
            and variant.economics.expected_net_monthly_eur_high
            and variant.economics.expected_net_monthly_eur_high < profile.target_net_monthly_eur
        ):
            cons.append("reason.economics.below_target")
        if regulated_level == "high":
            cons.append("reason.legal.high_regulated")
        elif regulated_level == "medium":
            cons.append("reason.legal.medium_regulated")
        if is_stale_warn:
            cons.append("reason.staleness.warn")
        if is_regulated:
            if not review_entry or review_entry.status != "verified":
                blockers.append("reason.review.requires_verification")
            elif review_verified_at is None:
                blockers.append("reason.review.missing_verified_at")
            else:
                review_days = (today - review_verified_at).days
                if review_days > policy.warn_after_days:
                    cons.append("reason.review.stale_warn")
                if review_days > policy.force_require_check_after_days:
                    blockers.append("reason.review.stale_force")
            if (
                appdata.rulepack.is_placeholder
                and review_entry
                and review_entry.status == "verified"
            ):
                has_evidence = False
                if review_entry.evidence_refs:
                    has_evidence = any(ref in evidence_ids for ref in review_entry.evidence_refs)
                if not has_evidence:
                    blockers.append("reason.review.requires_verification")

        blockers.extend(rule_eval.blockers)
        if is_regulated and is_stale_force:
            blockers.append("reason.legal.force_check")

        if appdata.rulepack.is_placeholder and is_regulated:
            verified_with_evidence = (
                review_entry is not None
                and review_entry.status == "verified"
                and bool(review_entry.evidence_refs)
                and any(ref in evidence_ids for ref in review_entry.evidence_refs)
            )
            if verified_with_evidence:
                blockers = [item for item in blockers if item != "reason.review.requires_verification"]
            elif "reason.review.requires_verification" not in blockers:
                blockers.append("reason.review.requires_verification")

        assumptions = _assumptions_for_variant(variant)

        ranked.append(
            RankedVariant(
                variant_id=variant.variant_id,
                score_total=round(score_total, 2),
                score_breakdown=score_breakdown,
                pros=pros[:3],
                cons=cons[:2],
                blockers=blockers[:3],
                assumptions=assumptions[:3],
                compliance_summary={
                    "required_kits": rule_eval.required_kits,
                    "regulated_level": regulated_level,
                    "warnings": rule_eval.warnings,
                },
                staleness={
                    "is_stale_warn": is_stale_warn,
                    "is_stale_force_check": is_stale_force,
                    "days_since_review": days_since_review,
                },
            )
        )

    ranked.sort(key=lambda item: (-item.score_total, item.variant_id))
    ranked = ranked[:top_n]

    diagnostics = {
        "profile_country": profile.country_code,
        "ranked_count": len(ranked),
        "staleness_days": {
            "dataset": meta_days,
            "rulepack": rulepack_days,
        },
    }
    return RecommendationResult(ranked_variants=ranked, diagnostics=diagnostics)

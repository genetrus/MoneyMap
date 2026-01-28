from __future__ import annotations

from datetime import date, datetime

from money_map.core.load import AppData
from money_map.core.model import RecommendationResult, UserProfile


def _to_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.today()


def recommend(profile: UserProfile, appdata: AppData, top_n: int) -> RecommendationResult:
    policy = appdata.meta.staleness_policy
    today = date.today()
    meta_days = (today - _to_date(appdata.meta.reviewed_at)).days
    rulepack_days = (today - _to_date(appdata.rulepack.reviewed_at)).days
    is_stale = meta_days > policy.warn_after_days
    require_check = (
        meta_days > policy.force_require_check_after_days
        or rulepack_days > policy.force_require_check_after_days
    )
    regulated_tags = set(policy.regulated_tags)

    sorted_variants = sorted(appdata.variants, key=lambda variant: variant.variant_id)
    ranked: list[dict] = []
    for variant in sorted_variants[:top_n]:
        has_regulated = bool(regulated_tags.intersection(variant.tags))
        ranked.append(
            {
                "variant_id": variant.variant_id,
                "pro_reasons": [
                    "Low operational complexity (stub)",
                    "Fits offline-first workflow (stub)",
                    "Matches profile constraints (stub)",
                ],
                "con_reason": "Requires further validation (stub)",
                "staleness": {
                    "dataset_stale": is_stale,
                    "requires_check": require_check and has_regulated,
                },
                "feasibility": variant.feasibility or {"status": "stub"},
                "economics": variant.economics or {"status": "stub"},
                "legal": variant.legal or {"status": "stub"},
            }
        )

    diagnostics = {
        "profile_country": profile.country_code,
        "ranked_count": len(ranked),
        "staleness_days": {
            "dataset": meta_days,
            "rulepack": rulepack_days,
        },
    }
    return RecommendationResult(ranked_variants=ranked, diagnostics=diagnostics)

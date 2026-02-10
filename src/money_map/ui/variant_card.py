"""Variant card helpers for Explore UI."""

from __future__ import annotations

import re
from dataclasses import dataclass

from money_map.core.model import Variant

_FORBIDDEN_PROMISE_PATTERNS = (
    r"\bguaranteed\b",
    r"\byou will definitely earn\b",
    r"\bstable\s*\d+\s*€",
)


@dataclass(frozen=True)
class ExploreCardCopy:
    title: str
    variant_id: str
    taxonomy: str
    cell: str
    one_liner: str
    feasibility_status: str
    prep_range: str
    blockers: list[str]
    prep_steps: list[str]
    ttfm_range: str
    net_range: str
    legal_gate: str
    legal_checks: list[str]
    pros: list[str]
    cons: list[str]
    reviewed_at: str
    stale_badge: str


def _limit_chars(value: str, max_chars: int) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return f"{cleaned[: max_chars - 1].rstrip()}…"


def _limit_words(value: str, max_words: int) -> str:
    words = value.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(".,;:") + "…"


def _replace_income_promises(value: str) -> str:
    text = value
    for pattern in _FORBIDDEN_PROMISE_PATTERNS:
        text = re.sub(pattern, "estimated", text, flags=re.IGNORECASE)
    return text


def _format_range(values: list[int] | None, unit: str, suffix: str = "") -> str:
    if not values or len(values) < 2:
        return "unknown"
    return f"{values[0]}–{values[1]} {unit}{suffix}".strip()


def _derive_blockers(variant: Variant) -> list[str]:
    blockers: list[str] = []
    required_assets = variant.feasibility.get("required_assets") or []
    if required_assets:
        blockers.append(f"Need assets: {', '.join(required_assets)}")
    min_lang = variant.feasibility.get("min_language_level")
    if min_lang:
        blockers.append(f"Language floor: {min_lang}")
    legal_gate = str(variant.legal.get("legal_gate", "ok"))
    if legal_gate != "ok":
        blockers.append("Legal review required before launch")
    if not blockers:
        blockers.append("No hard blockers in current data")
    return [_limit_words(item, 10) for item in blockers[:3]]


def build_explore_card_copy(
    variant: Variant,
    *,
    taxonomy: str,
    cell: str,
    stale: bool,
) -> ExploreCardCopy:
    summary = _replace_income_promises(variant.summary)
    one_liner = _limit_chars(summary, 160)
    prep_steps = [_limit_words(step, 10) for step in (variant.prep_steps or [])[:5]]
    if not prep_steps:
        prep_steps = ["Add prep steps from dataset"]

    ttfm = variant.economics.get("time_to_first_money_days_range")
    net_month = variant.economics.get("typical_net_month_eur_range")
    legal_checks = variant.legal.get("checklist") or ["Verify local legal requirements"]
    legal_checks = [_limit_words(str(item), 10) for item in legal_checks[:6]]

    pros = [
        _limit_words(f"TTFM estimate: {_format_range(ttfm, 'days')}", 12),
        _limit_words(f"Net/month estimate: €{_format_range(net_month, '')}", 12),
        _limit_words(f"Legal gate: {variant.legal.get('legal_gate', 'ok')}", 12),
    ]
    cons = []
    if variant.legal.get("legal_gate", "ok") != "ok":
        cons.append(_limit_words("Legal gate is not ok, requires checks", 14))
    confidence = str(variant.economics.get("confidence", "unknown"))
    if confidence == "low":
        cons.append(_limit_words("Economics confidence is low in current dataset", 14))
    if not cons:
        cons.append(_limit_words("Ranges are estimates, not income guarantees", 14))

    prep_range = "unknown"
    min_hours = variant.feasibility.get("min_time_per_week")
    if isinstance(min_hours, int):
        prep_range = f"~{max(1, min_hours // 4)}–{max(2, min_hours // 2)} weeks (estimate)"

    stale_badge = "warn" if stale else "fresh"
    return ExploreCardCopy(
        title=variant.title,
        variant_id=variant.variant_id,
        taxonomy=taxonomy,
        cell=cell,
        one_liner=one_liner,
        feasibility_status="feasible_with_prep" if prep_steps else "feasible",
        prep_range=prep_range,
        blockers=_derive_blockers(variant),
        prep_steps=prep_steps,
        ttfm_range=_format_range(ttfm, "days", " (estimate)"),
        net_range=f"€{_format_range(net_month, '', '/mo net estimate')}",
        legal_gate=str(variant.legal.get("legal_gate", "ok")),
        legal_checks=legal_checks,
        pros=pros,
        cons=cons[:2],
        reviewed_at=variant.review_date or "unknown",
        stale_badge=stale_badge,
    )


def has_income_promise(text: str) -> bool:
    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in _FORBIDDEN_PROMISE_PATTERNS
    )

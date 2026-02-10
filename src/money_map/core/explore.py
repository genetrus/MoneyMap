"""Deterministic Explore helpers shared by acceptance checks and UI."""

from __future__ import annotations

from money_map.core.model import AppData, Variant

BRIDGE_OPTIONS = ("A1->A2", "A2->B2", "A1->B1", "B1->B2")


def stable_variant_sort_key(variant: Variant) -> tuple[int, str]:
    ttfm = variant.economics.get("time_to_first_money_days_range") or []
    ttfm_min = ttfm[0] if ttfm else 10**9
    return (int(ttfm_min), variant.variant_id)


def variant_taxonomy_from_tags(variant: Variant) -> str:
    tags = set(variant.tags)
    if "writing" in tags:
        return "service_fee"
    if "physical" in tags:
        return "labor"
    if "regulated" in tags:
        return "commission"
    if "remote" in tags:
        return "subscription"
    return "service_fee"


def variant_cell_from_tags(variant: Variant) -> str:
    tags = set(variant.tags)
    if "remote" in tags and "regulated" in tags:
        return "B2"
    if "remote" in tags:
        return "A2"
    if "regulated" in tags:
        return "B1"
    return "A1"


def explore_cell_candidates(app_data: AppData, cell: str, limit: int = 3) -> list[Variant]:
    variants = sorted(app_data.variants, key=stable_variant_sort_key)
    candidates = [variant for variant in variants if variant_cell_from_tags(variant) == cell]
    return candidates[:limit]


def explore_bridge_candidates(app_data: AppData, bridge: str, limit: int = 3) -> list[Variant]:
    frm, to = bridge.split("->", 1)
    variants = sorted(app_data.variants, key=stable_variant_sort_key)
    candidates = [variant for variant in variants if variant_cell_from_tags(variant) in {frm, to}]
    return candidates[:limit]

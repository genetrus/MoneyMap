"""Centralized projection/session state for Streamlit UI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

PROFILE_KEY = "profile"
FILTERS_KEY = "projection_filters"
SELECTION_KEY = "projection_selection"
RECOMMENDATION_KEY = "projection_recommendation"
PLAN_KEY = "projection_plan"
EXPORT_PATHS_KEY = "export_paths"

DEFAULT_FILTERS = {
    "top_n": 10,
    "max_risk": 1.0,
    "max_legal_friction": 4,
    "startability_window": 14,
    "allowed_legal_gates": ["ok", "require_check", "registration", "license"],
    "allowed_feasibility_status": ["feasible", "feasible_with_prep"],
    "include_tags": [],
    "exclude_tags": [],
    "max_time_to_first_money_days": 365,
    "min_typical_net_month": 0,
    "compliance_mode": "include_with_prep",
}


@dataclass
class ProfileState:
    payload: dict[str, Any]


@dataclass
class FiltersState:
    top_n: int
    max_risk: float
    max_legal_friction: int
    startability_window: int
    allowed_legal_gates: list[str]
    allowed_feasibility_status: list[str]
    include_tags: list[str]
    exclude_tags: list[str]
    max_time_to_first_money_days: int
    min_typical_net_month: int
    compliance_mode: str


@dataclass
class SelectionState:
    selected_variant_id: str
    selected_source: str


@dataclass
class RecommendationState:
    result: Any | None
    cache_key: str


@dataclass
class PlanState:
    route_plan: Any | None
    cache_key: str


def _state():
    import streamlit as st

    return st.session_state


def ensure_defaults(default_profile: dict[str, Any]) -> None:
    state = _state()
    state.setdefault(PROFILE_KEY, default_profile.copy())
    state.setdefault(FILTERS_KEY, DEFAULT_FILTERS.copy())
    state.setdefault(SELECTION_KEY, asdict(SelectionState("", "")))
    state.setdefault(RECOMMENDATION_KEY, asdict(RecommendationState(None, "")))
    state.setdefault(PLAN_KEY, asdict(PlanState(None, "")))
    state.setdefault(EXPORT_PATHS_KEY, None)


def get_profile() -> ProfileState:
    return ProfileState(payload=dict(_state().get(PROFILE_KEY, {})))


def set_profile(profile: dict[str, Any]) -> None:
    _state()[PROFILE_KEY] = profile
    invalidate_recommendation()


def get_filters() -> FiltersState:
    raw = dict(DEFAULT_FILTERS)
    raw.update(_state().get(FILTERS_KEY, {}))
    return FiltersState(**raw)


def set_filters(filters: FiltersState | dict[str, Any]) -> None:
    payload = asdict(filters) if isinstance(filters, FiltersState) else dict(filters)
    merged = dict(DEFAULT_FILTERS)
    merged.update(payload)
    _state()[FILTERS_KEY] = merged
    invalidate_recommendation()


def get_selection() -> SelectionState:
    raw = _state().get(SELECTION_KEY, {})
    return SelectionState(
        selected_variant_id=raw.get("selected_variant_id", ""),
        selected_source=raw.get("selected_source", ""),
    )


def set_selection(selected_variant_id: str, selected_source: str = "") -> None:
    _state()[SELECTION_KEY] = asdict(SelectionState(selected_variant_id, selected_source))
    invalidate_plan()


def get_recommendation_state() -> RecommendationState:
    raw = _state().get(RECOMMENDATION_KEY, {})
    return RecommendationState(result=raw.get("result"), cache_key=raw.get("cache_key", ""))


def set_recommendation_state(result: Any, cache_key: str) -> None:
    _state()[RECOMMENDATION_KEY] = asdict(RecommendationState(result=result, cache_key=cache_key))


def get_plan_state() -> PlanState:
    raw = _state().get(PLAN_KEY, {})
    return PlanState(route_plan=raw.get("route_plan"), cache_key=raw.get("cache_key", ""))


def set_plan_state(route_plan: Any, cache_key: str) -> None:
    _state()[PLAN_KEY] = asdict(PlanState(route_plan=route_plan, cache_key=cache_key))


def invalidate_recommendation() -> None:
    _state()[RECOMMENDATION_KEY] = asdict(RecommendationState(None, ""))
    invalidate_plan()


def invalidate_plan() -> None:
    _state()[PLAN_KEY] = asdict(PlanState(None, ""))
    _state()[EXPORT_PATHS_KEY] = None


def compute_profile_hash(profile: dict[str, Any], filters: FiltersState | dict[str, Any]) -> str:
    payload = {
        "profile": profile,
        "filters": asdict(filters) if isinstance(filters, FiltersState) else filters,
    }
    return sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()


SESSION_KEYS = [
    PROFILE_KEY,
    FILTERS_KEY,
    SELECTION_KEY,
    RECOMMENDATION_KEY,
    PLAN_KEY,
    EXPORT_PATHS_KEY,
]

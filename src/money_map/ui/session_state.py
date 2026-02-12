"""Session state schema and reset rules for MoneyMap UI."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, MutableMapping

DEFAULT_FILTERS: dict[str, Any] = {
    "top_n": 10,
    "max_risk": "any",
    "max_legal_friction": "any",
    "startability_window_days": 60,
    "include_cells": [],
    "include_taxonomy": [],
    "include_tags": {"sell": [], "to_whom": [], "value": []},
    "exclude_tags": {"sell": [], "to_whom": [], "value": []},
    # Backward-compatible flags used by current recommender implementation.
    "exclude_blocked": True,
    "exclude_not_feasible": False,
    "max_time_to_money_days": 60,
}

SESSION_DEFAULTS: dict[str, Any] = {
    "app_run_id": "",
    "data_dir": "data",
    "dataset_version": "",
    "rulepack_country": "DE",
    "rulepack_reviewed_at": "",
    "staleness_level": "WARN",
    "view_mode": "User",
    "page": "data-status",
    "subview": "",
    "selected_cell_id": "",
    "selected_taxonomy_id": "",
    "selected_variant_id": "",
    "selected_bridge_id": "",
    "selected_path_id": "",
    "profile": None,
    "profile_hash": "",
    "objective_preset": "fastest_money",
    "filters": DEFAULT_FILTERS,
    "filters_hash": "",
    "validate_report": None,
    "explore_cache": {},
    "recommendations": None,
    "recommend_diagnostics": None,
    "plan": None,
    "export_paths": None,
    "dataset_signature": "",
    "guide_state": {
        "enabled": True,
        "current_step_id": "step_data_status",
        "completed_steps": [],
        "skipped_steps": [],
        "dismissed_tooltips": [],
    },
    "guide_entities": {
        "data_valid": False,
        "profile_status": "missing",
        "selected_variant_id": None,
        "plan_ready": False,
        "exports_ready": False,
    },
}

RESET_ON_DATASET_CHANGE = [
    "page",
    "subview",
    "selected_cell_id",
    "selected_taxonomy_id",
    "selected_variant_id",
    "selected_bridge_id",
    "selected_path_id",
    "profile",
    "profile_hash",
    "objective_preset",
    "filters",
    "filters_hash",
    "validate_report",
    "explore_cache",
    "recommendations",
    "recommend_diagnostics",
    "plan",
    "export_paths",
    "guide_entities",
]


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_filters_hash(filters: dict[str, Any]) -> str:
    payload = _stable_json(filters)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_dataset_signature(*, data_dir: str, dataset_version: str, reviewed_at: str) -> str:
    return f"{data_dir}|{dataset_version}|{reviewed_at}"


def initialize_defaults(state: MutableMapping[str, Any]) -> None:
    for key, default in SESSION_DEFAULTS.items():
        if key not in state:
            state[key] = deepcopy(default)


def reset_downstream_for_profile_change(state: MutableMapping[str, Any]) -> None:
    state["selected_variant_id"] = ""
    state["plan"] = None
    state["recommendations"] = None
    state["recommend_diagnostics"] = None
    state["last_recommendations"] = None


def sync_filters_and_objective(
    state: MutableMapping[str, Any],
    *,
    filters: dict[str, Any],
    objective_preset: str,
) -> bool:
    new_filters_hash = compute_filters_hash(filters)
    previous_filters_hash = state.get("filters_hash", "")
    previous_objective = state.get("objective_preset", "")

    state["filters"] = filters
    state["filters_hash"] = new_filters_hash
    state["objective_preset"] = objective_preset

    changed = (new_filters_hash != previous_filters_hash) or (
        objective_preset != previous_objective
    )
    if changed:
        state["recommendations"] = None
        state["recommend_diagnostics"] = None
        state["last_recommendations"] = None
        state["plan"] = None
    return changed


def sync_dataset_meta(
    state: MutableMapping[str, Any],
    *,
    data_dir: str,
    dataset_version: str,
    reviewed_at: str,
    staleness_level: str,
    country: str = "DE",
) -> bool:
    new_signature = compute_dataset_signature(
        data_dir=data_dir,
        dataset_version=dataset_version,
        reviewed_at=reviewed_at,
    )
    previous_signature = state.get("dataset_signature", "")

    state["data_dir"] = data_dir
    state["dataset_version"] = dataset_version
    state["rulepack_country"] = country
    state["rulepack_reviewed_at"] = reviewed_at
    state["staleness_level"] = staleness_level.upper()
    state["dataset_signature"] = new_signature

    changed = bool(previous_signature) and previous_signature != new_signature
    if changed:
        preserved_view_mode = state.get("view_mode", "User")
        for key in RESET_ON_DATASET_CHANGE:
            if key in SESSION_DEFAULTS:
                state[key] = deepcopy(SESSION_DEFAULTS[key])
            else:
                state[key] = None
        state["view_mode"] = preserved_view_mode
        state["data_dir"] = data_dir
        state["dataset_version"] = dataset_version
        state["rulepack_country"] = country
        state["rulepack_reviewed_at"] = reviewed_at
        state["staleness_level"] = staleness_level.upper()
        state["dataset_signature"] = new_signature
    return changed

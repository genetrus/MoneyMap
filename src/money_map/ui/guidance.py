"""Next-step guidance engine for Guided/Explorer UX modes."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, MutableMapping

import yaml

from money_map.core.profile import validate_profile

_GUIDE_PATH = Path("data/ui_guides/onboarding_ru.yaml")

GUIDE_STATE_DEFAULTS: dict[str, Any] = {
    "enabled": True,
    "current_step_id": "step_data_status",
    "completed_steps": [],
    "skipped_steps": [],
    "dismissed_tooltips": [],
}

BLOCKER_TEXT = {
    "data_valid == true": "Данные невалидны: открой Data status и исправь FATAL/FAIL.",
    "profile_status == 'ready'": "Профиль не готов: заполни обязательные поля.",
    "selected_variant_id != null": "Сначала выбери вариант в Recommendations.",
    "plan_ready == true": "Сначала построй план на экране Plan.",
    "exports_ready == true": "Сначала сформируй экспортные файлы.",
}


def initialize_guide_state(state: MutableMapping[str, Any]) -> dict[str, Any]:
    raw = state.get("guide_state")
    if not isinstance(raw, dict):
        state["guide_state"] = deepcopy(GUIDE_STATE_DEFAULTS)
        return state["guide_state"]

    normalized = deepcopy(GUIDE_STATE_DEFAULTS)
    normalized.update(raw)
    normalized["enabled"] = bool(normalized.get("enabled", True))
    normalized["completed_steps"] = _normalize_str_list(normalized.get("completed_steps"))
    normalized["skipped_steps"] = _normalize_str_list(normalized.get("skipped_steps"))
    normalized["dismissed_tooltips"] = _normalize_str_list(normalized.get("dismissed_tooltips"))

    valid_ids = set(step["id"] for step in load_guide_steps())
    current_step_id = str(normalized.get("current_step_id") or "")
    if current_step_id not in valid_ids:
        normalized["current_step_id"] = load_guide_steps()[0]["id"]

    state["guide_state"] = normalized
    return normalized


@lru_cache(maxsize=1)
def load_guide_steps() -> list[dict[str, Any]]:
    if not _GUIDE_PATH.exists():
        return []
    payload = yaml.safe_load(_GUIDE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    steps = payload.get("steps")
    if not isinstance(steps, list):
        return []

    normalized: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        if not step.get("id") or not step.get("page"):
            continue
        normalized.append(step)
    return normalized


def compute_guidance_runtime(
    state: MutableMapping[str, Any],
    *,
    validate_report: dict[str, Any] | None,
) -> dict[str, Any]:
    guide_state = initialize_guide_state(state)
    steps = load_guide_steps()
    entities = _collect_entities(state, validate_report=validate_report)

    completed_steps: list[str] = []
    for step in steps:
        completion = step.get("completion") or []
        if _all_predicates_true(completion, entities):
            completed_steps.append(str(step["id"]))

    skipped_steps = [
        step_id
        for step_id in guide_state["skipped_steps"]
        if any(str(step["id"]) == step_id for step in steps)
    ]

    pending_steps = [
        step
        for step in steps
        if step["id"] not in completed_steps and step["id"] not in skipped_steps
    ]
    current_step = pending_steps[0] if pending_steps else (steps[-1] if steps else {})

    prerequisites = current_step.get("prerequisites") or []
    completion = current_step.get("completion") or []
    blockers = _blockers(prerequisites, entities) + _blockers(completion, entities)
    # keep order, remove duplicates
    deduped_blockers: list[str] = []
    for item in blockers:
        if item not in deduped_blockers:
            deduped_blockers.append(item)
    blockers = deduped_blockers
    blocked = bool(blockers)

    primary_action = current_step.get("primary_action") or {}
    if not isinstance(primary_action, dict):
        primary_action = {}
    primary_action = {
        "label": str(primary_action.get("label") or "Continue"),
        "action_key": str(primary_action.get("action_key") or "continue"),
        "target_page": str(primary_action.get("target_page") or current_step.get("page") or ""),
        "disabled": blocked,
    }

    blockers_resolver = current_step.get("blockers_resolver") or {}
    if not isinstance(blockers_resolver, dict):
        blockers_resolver = {}
    blockers_resolver = {
        "focus_page": str(blockers_resolver.get("focus_page") or current_step.get("page") or ""),
        "highlight_fields": _normalize_str_list(blockers_resolver.get("highlight_fields")),
    }

    guide_state["completed_steps"] = completed_steps
    guide_state["current_step_id"] = str(
        current_step.get("id") or GUIDE_STATE_DEFAULTS["current_step_id"]
    )

    runtime = {
        "entities": entities,
        "is_guided": bool(guide_state["enabled"]),
        "current_step": current_step,
        "next_step": current_step,
        "blockers": blockers,
        "primary_action": primary_action,
        "blockers_resolver": blockers_resolver,
    }
    state["guidance_runtime"] = runtime
    return runtime


def _collect_entities(
    state: MutableMapping[str, Any],
    *,
    validate_report: dict[str, Any] | None,
) -> dict[str, Any]:
    report_status = str((validate_report or {}).get("status", "invalid")).lower()
    data_valid = report_status in {"valid", "stale"}

    profile = state.get("profile")
    profile_validation = validate_profile(profile if isinstance(profile, dict) else {})
    if profile_validation["is_ready"]:
        profile_status = "ready"
    elif profile_validation["missing"]:
        profile_status = "missing"
    else:
        profile_status = "draft"

    selected_variant_id = str(state.get("selected_variant_id") or "")
    plan_ready = _is_plan_ready(state.get("plan"))
    exports_ready = _is_exports_ready(state.get("export_paths"))

    entities = {
        "data_valid": data_valid,
        "profile_status": profile_status,
        "selected_variant_id": selected_variant_id or None,
        "plan_ready": plan_ready,
        "exports_ready": exports_ready,
    }
    state["guide_entities"] = entities
    return entities


def _all_predicates_true(predicates: list[Any], entities: dict[str, Any]) -> bool:
    if not predicates:
        return False
    return all(_predicate_true(str(predicate), entities) for predicate in predicates)


def _blockers(predicates: list[Any], entities: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    for predicate in predicates:
        raw = str(predicate)
        if not _predicate_true(raw, entities):
            blockers.append(BLOCKER_TEXT.get(raw, f"Не выполнено условие: {raw}"))
    return blockers


def _predicate_true(predicate: str, entities: dict[str, Any]) -> bool:
    normalized = predicate.strip()
    if "==" in normalized:
        left, right = [item.strip() for item in normalized.split("==", 1)]
        return _entity_value(left, entities) == _parse_literal(right)
    if "!=" in normalized:
        left, right = [item.strip() for item in normalized.split("!=", 1)]
        return _entity_value(left, entities) != _parse_literal(right)
    return bool(_entity_value(normalized, entities))


def _entity_value(name: str, entities: dict[str, Any]) -> Any:
    return entities.get(name)


def _parse_literal(raw: str) -> Any:
    value = raw.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None"}:
        return None
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]
    return value


def _normalize_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        text = str(item).strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def _is_plan_ready(plan: Any) -> bool:
    if plan is None:
        return False

    steps = _value_from(plan, "steps")
    artifacts = _value_from(plan, "artifacts")
    week_plan = _value_from(plan, "week_plan")
    compliance = _value_from(plan, "compliance")
    legal_gate = str(_value_from(plan, "legal_gate") or "").strip().lower()

    has_steps = bool(steps)
    has_artifacts = bool(artifacts)
    has_compliance = bool(compliance)
    has_4_week_coverage = _has_4_week_coverage(week_plan)
    requires_compliance = legal_gate != "ok"

    if not (has_steps and has_artifacts and has_4_week_coverage):
        return False
    if requires_compliance and not has_compliance:
        return False
    return True


def _has_4_week_coverage(week_plan: Any) -> bool:
    if not isinstance(week_plan, dict):
        return False
    if len(week_plan) < 4:
        return False

    covered_weeks: set[int] = set()
    for key in week_plan:
        week_num = _parse_week_number(str(key))
        if week_num is not None and 1 <= week_num <= 4:
            covered_weeks.add(week_num)
    return covered_weeks == {1, 2, 3, 4}


def _parse_week_number(raw_key: str) -> int | None:
    digits = "".join(ch for ch in raw_key if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _is_exports_ready(export_paths: Any) -> bool:
    if not isinstance(export_paths, dict):
        return False

    required_keys = ["plan", "result", "profile"]
    for key in required_keys:
        value = export_paths.get(key)
        if not isinstance(value, str) or not value.strip():
            return False
    return True


def _value_from(container: Any, key: str) -> Any:
    if isinstance(container, dict):
        return container.get(key)
    return getattr(container, key, None)

"""Streamlit UI for MoneyMap walking skeleton."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from uuid import uuid4

import streamlit as st
import yaml

from money_map.app.api import export_bundle
from money_map.core.classify import classify_idea_text
from money_map.core.errors import InternalError, MoneyMapError
from money_map.core.graph import build_plan
from money_map.core.load import load_app_data
from money_map.core.profile import (
    profile_hash as compute_profile_hash,
)
from money_map.core.profile import (
    profile_reproducibility_state,
    validate_profile,
)
from money_map.core.recommend import is_variant_stale, recommend
from money_map.core.validate import validate
from money_map.render.plan_md import render_plan_md
from money_map.render.result_json import render_result_json
from money_map.storage.fs import read_yaml
from money_map.ui.components import (
    render_badge_set,
    render_context_bar,
    render_detail_drawer,
    action_contract_help,
    build_action_contract,
    render_empty_state,
    render_filter_chips_bar,
    render_graph_fallback,
    render_guide_panel,
    render_header_bar,
    render_info_callout,
    render_inline_hint,
    render_kpi_grid,
    render_tooltip,
    selected_ids_from_state,
)
from money_map.ui.copy import copy_text
from money_map.ui.data_status import (
    aggregate_pack_metrics,
    build_validate_rows,
    data_status_visibility,
    filter_validate_rows,
    oldest_stale_entities,
    variants_by_cell,
    variants_by_legal_gate,
)
from money_map.ui.guidance import compute_guidance_runtime, initialize_guide_state
from money_map.ui.jobs_live import create_variant_draft, resolve_jobs_source
from money_map.ui.navigation import (
    NAV_ITEMS,
    NAV_LABEL_BY_SLUG,
    resolve_page_from_query,
)
from money_map.ui.session_state import (
    DEFAULT_FILTERS,
    compute_filters_hash,
    initialize_defaults,
    reset_downstream_for_profile_change,
    sync_dataset_meta,
    sync_filters_and_objective,
)
from money_map.ui.theme import inject_global_theme
from money_map.ui.variant_card import build_explore_card_copy
from money_map.ui.view_mode import get_view_mode, render_view_mode_control

CELL_OPTIONS = ["A1", "A2", "B1", "B2"]
TAXONOMY_OPTIONS = [
    "service_fee",
    "labor",
    "asset_rental",
    "resale_margin",
    "commission",
    "subscription",
]
BRIDGE_OPTIONS = ["A1->A2", "A2->B2", "A1->B1", "B1->B2"]


def _stable_variant_sort_key(variant) -> tuple[int, str]:
    ttfm = variant.economics.get("time_to_first_money_days_range") or []
    ttfm_min = ttfm[0] if ttfm else 10**9
    return (int(ttfm_min), variant.variant_id)


def _variant_taxonomy(variant) -> str:
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


def _variant_cell(variant) -> str:
    tags = set(variant.tags)
    if "remote" in tags and "regulated" in tags:
        return "B2"
    if "remote" in tags:
        return "A2"
    if "regulated" in tags:
        return "B1"
    return "A1"


def _render_explore_variant_card(variant, *, taxonomy: str, cell: str, stale: bool) -> None:
    card = build_explore_card_copy(variant, taxonomy=taxonomy, cell=cell, stale=stale)

    st.markdown(f"### {card.title} · {card.variant_id}")
    st.markdown(f"**Taxonomy:** {card.taxonomy} · **Cell:** {card.cell}")
    st.markdown(
        f"**Status:** {card.feasibility_status} · **Legal gate:** {card.legal_gate} "
        f"· **Staleness:** {card.stale_badge}"
    )
    render_badge_set(
        feasibility=card.feasibility_status,
        legal_gate=card.legal_gate,
        staleness=card.stale_badge,
        confidence=variant.economics.get("confidence", "unknown"),
    )
    st.markdown(f"**Summary:** {card.one_liner}")

    with st.expander("Подробнее", expanded=False):
        st.markdown("#### 1) Feasibility")
        st.markdown(f"- **Status:** {card.feasibility_status}")
        st.markdown(f"- **Prep:** {card.prep_range}")
        st.markdown("- **Blockers:**")
        for item in card.blockers:
            st.markdown(f"  - {item}")
        st.markdown("- **Prep steps:**")
        for item in card.prep_steps:
            st.markdown(f"  - {item}")

        st.markdown("#### 2) Economics *(estimate, not guarantee)*")
        st.markdown(f"- **TTFM:** {card.ttfm_range}")
        st.markdown(f"- **Net/month:** {card.net_range}")

        st.markdown("#### 3) Legal / Compliance *(requires verification)*")
        st.markdown(f"- **Gate:** {card.legal_gate}")
        for item in card.legal_checks:
            st.markdown(f"  - {item}")

        st.markdown("#### 4) Why / Why not")
        st.markdown("- **Pros (3):**")
        for item in card.pros:
            st.markdown(f"  - {item}")
        st.markdown("- **Cons (1–2):**")
        for item in card.cons:
            st.markdown(f"  - {item}")

        st.markdown("#### 5) Evidence & Staleness")
        st.markdown(f"- Reviewed: {card.reviewed_at}")
        st.markdown(f"- Staleness: {card.stale_badge}")

        st.markdown("#### 6) Actions")
        st.markdown("- [ ] Open in Explore")
        st.markdown("- [ ] Use as Recommendations filter")


DEFAULT_PROFILE = {
    "name": "Demo",
    "country": "DE",
    "location": "Berlin",
    "objective": "fastest_money",
    "language_level": "B1",
    "capital_eur": 300,
    "time_per_week": 15,
    "assets": ["laptop", "phone"],
    "skills": ["customer_service"],
    "constraints": ["no_night_shifts"],
}


def _normalize_profile(raw_profile: object) -> dict:
    if not isinstance(raw_profile, dict):
        return DEFAULT_PROFILE.copy()

    normalized = DEFAULT_PROFILE.copy()
    normalized.update(raw_profile)
    return normalized


def _normalize_filters(raw_filters: object) -> dict:
    if not isinstance(raw_filters, dict):
        return DEFAULT_FILTERS.copy()

    normalized = DEFAULT_FILTERS.copy()
    normalized.update(raw_filters)
    return normalized


def _init_state() -> None:
    initialize_defaults(st.session_state)
    st.session_state["profile"] = _normalize_profile(st.session_state.get("profile"))
    st.session_state["filters"] = _normalize_filters(st.session_state.get("filters"))
    st.session_state.setdefault("last_recommendations", None)
    st.session_state.setdefault("profile_source", "Demo profile")
    st.session_state.setdefault("ui_run_id", str(uuid4()))
    st.session_state.setdefault("theme_preset", "Light")
    st.session_state.setdefault("profile_quick_mode", True)
    st.session_state.setdefault(
        "objective_preset", st.session_state["profile"].get("objective", "fastest_money")
    )
    st.session_state.setdefault("profile_hash", compute_profile_hash(st.session_state["profile"]))
    st.session_state.setdefault("page_initialized", False)
    st.session_state.setdefault("explore_tab", "Matrix")
    st.session_state.setdefault("explore_selected_cell", "A1")
    st.session_state.setdefault("explore_selected_taxonomy", "service_fee")
    st.session_state.setdefault("explore_selected_bridge", "A1->A2")
    st.session_state.setdefault("explore_paths_enabled", False)
    st.session_state.setdefault("explore_library_enabled", False)
    st.session_state.setdefault("classify_idea_text", "")
    st.session_state.setdefault("classify_result", None)
    st.session_state.setdefault("classify_error", "")
    st.session_state.setdefault("classify_selected_variant_id", "")
    st.session_state.setdefault("classify_prefilter", {})
    st.session_state.setdefault("jobs_variant_drafts", [])
    st.session_state.setdefault("jobs_last_source", {})
    initialize_guide_state(st.session_state)
    st.session_state["filters_hash"] = compute_filters_hash(st.session_state["filters"])


def _render_error(err: MoneyMapError) -> None:
    run_id = err.run_id or st.session_state.get("ui_run_id", "unknown")
    reasons = []
    if err.hint:
        reasons.append(f"Hint: {err.hint}")
    if err.details:
        reasons.append(f"Details: {err.details}")
    reasons.append(f"run_id: {run_id}")
    _render_status("error", f"{err.code}: {err.message}", reasons=reasons, level="error")


def _render_status(
    status: str,
    message: str,
    *,
    reasons: list[str] | None = None,
    level: str = "info",
) -> None:
    header = f"Status: {status} — {message}"
    if level == "error":
        st.error(header)
    elif level == "warning":
        st.warning(header)
    else:
        st.info(header)
    if reasons:
        for reason in reasons:
            st.caption(f"Reason: {reason}")


def _run_with_error_boundary(action) -> None:
    try:
        action()
    except MoneyMapError as exc:
        _render_error(exc)
        st.stop()
    except Exception as exc:
        error = InternalError(
            message=str(exc) or "Unexpected error",
            hint="Review logs or retry the action.",
            run_id=st.session_state.get("ui_run_id"),
        )
        _render_error(error)
        st.stop()


@st.cache_resource
def _get_app_data():
    return load_app_data()


@st.cache_data
def _get_validation() -> dict:
    app_data = _get_app_data()
    report = validate(app_data)
    return {
        "status": report.status,
        "fatals": report.fatals,
        "warns": report.warns,
        "dataset_version": report.dataset_version,
        "reviewed_at": report.reviewed_at,
        "stale": report.stale,
        "staleness_policy_days": report.staleness_policy_days,
        "generated_at": report.generated_at,
        "staleness": report.staleness,
    }


@st.cache_data
def _get_recommendations(profile_json: str, objective: str, filters: dict, top_n: int):
    profile = json.loads(profile_json)
    app_data = _get_app_data()
    return recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        objective,
        filters,
        top_n,
    )


def _ensure_plan(profile: dict, variant_id: str):
    app_data = _get_app_data()
    variant = next((v for v in app_data.variants if v.variant_id == variant_id), None)
    if variant is None:
        raise ValueError(f"Variant '{variant_id}' not found.")
    return build_plan(profile, variant, app_data.rulepack, app_data.meta.staleness_policy)


def _sync_profile_session_state(profile: dict) -> None:
    reproducibility = profile_reproducibility_state(
        profile, previous_hash=st.session_state.get("profile_hash")
    )
    st.session_state["profile_hash"] = reproducibility["profile_hash"]
    st.session_state["objective_preset"] = reproducibility["objective_preset"]
    if reproducibility["changed"]:
        reset_downstream_for_profile_change(st.session_state)


def _ensure_objective(profile: dict, objective_options: list[str]) -> str:
    current = profile.get("objective")
    if current not in objective_options:
        current = "fastest_money"
        profile["objective"] = current
    return current


def _issue_codes(issues: list[dict]) -> list[str]:
    return [issue.get("code", "") for issue in issues if issue.get("code")]


def _issue_rows(issues: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for issue in issues:
        rows.append(
            {
                "Code": issue.get("code", ""),
                "Message": issue.get("message", ""),
                "Source": issue.get("source", ""),
                "Location": issue.get("location", ""),
                "Hint": issue.get("hint", ""),
            }
        )
    return rows


def _issue_summary(issues: list[dict], limit: int = 3) -> str | None:
    codes = _issue_codes(issues)
    if not codes:
        return None
    return ", ".join(codes[:limit])


def _guard_fatals(report: dict) -> None:
    if report["fatals"]:
        _render_status(
            "error",
            "Validation fatals block actions",
            reasons=[", ".join(_issue_codes(report["fatals"]))],
            level="error",
        )
        st.stop()


def _render_kpi_card(
    label: str,
    value: str,
    subtext: str | None = None,
    badge: str | None = None,
    badge_class: str | None = None,
    chip: str | None = None,
) -> None:
    badge_html = ""
    if badge and badge_class:
        badge_html = f'<span class="kpi-badge {badge_class}">{badge}</span>'
    chip_html = f'<span class="kpi-chip">{chip}</span>' if chip else ""
    subtext_html = f'<div class="kpi-subtext">{subtext}</div>' if subtext else ""
    st.markdown(
        """
        <div class="kpi-card">
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
          {badge_html}
          {subtext_html}
          {chip_html}
        </div>
        """.format(
            label=label,
            value=value,
            badge_html=badge_html,
            subtext_html=subtext_html,
            chip_html=chip_html,
        ),
        unsafe_allow_html=True,
    )


def _render_distribution_chart(title: str, rows: list[dict[str, int | str]]) -> None:
    st.markdown(f"**{title}**")
    if not rows:
        st.caption("No data for chart.")
        return
    st.vega_lite_chart(
        {
            "data": {"values": rows},
            "mark": "bar",
            "encoding": {
                "x": {"field": "label", "type": "nominal", "sort": "-y", "title": ""},
                "y": {"field": "count", "type": "quantitative", "title": "Count"},
                "tooltip": [
                    {"field": "label", "type": "nominal"},
                    {"field": "count", "type": "quantitative"},
                ],
            },
            "height": 240,
        },
        use_container_width=True,
    )


def _capital_band(capital_eur: int) -> str:
    if capital_eur <= 300:
        return "low"
    if capital_eur <= 1200:
        return "medium"
    return "high"


def _profile_preview_snapshot(profile: dict) -> dict[str, object]:
    app_data = _get_app_data()
    broad_filters = {
        "exclude_blocked": False,
        "exclude_not_feasible": False,
        "max_time_to_money_days": 365,
    }
    recs = recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        profile.get("objective", "fastest_money"),
        broad_filters,
        max(1, len(app_data.variants)),
    )

    ranked = recs.ranked_variants
    feasible_now = sum(1 for rec in ranked if rec.feasibility.status == "feasible")
    startable_2w = sum(
        1
        for rec in ranked
        if rec.feasibility.status != "not_feasible"
        and rec.economics.time_to_first_money_days_range
        and rec.economics.time_to_first_money_days_range[0] <= 14
    )
    low_legal_friction = sum(1 for rec in ranked if rec.legal.legal_gate in {"ok", "require_check"})

    cell_counts: dict[str, int] = {cell: 0 for cell in CELL_OPTIONS}
    for rec in ranked:
        if rec.feasibility.status in {"feasible", "feasible_with_prep"}:
            cell_counts[_variant_cell(rec.variant)] = (
                cell_counts.get(_variant_cell(rec.variant), 0) + 1
            )

    heatmap_rows = [{"cell": cell, "count": count} for cell, count in cell_counts.items()]
    return {
        "feasible_now": feasible_now,
        "startable_2w": startable_2w,
        "low_legal_friction": low_legal_friction,
        "heatmap_rows": heatmap_rows,
        "evaluated": len(ranked),
    }


def _render_profile_preview(preview: dict[str, object]) -> None:
    st.markdown("### Live preview")
    render_kpi_grid(
        [
            {"label": "Feasible now", "value": f"~{preview['feasible_now']} variants"},
            {"label": "Startable ≤2 weeks", "value": f"~{preview['startable_2w']}"},
            {"label": "Low legal friction", "value": f"~{preview['low_legal_friction']}"},
        ]
    )

    st.markdown("**Mini matrix heatmap (feasible by cell)**")
    rows = preview["heatmap_rows"]
    st.vega_lite_chart(
        {
            "data": {"values": rows},
            "mark": "rect",
            "encoding": {
                "x": {
                    "field": "cell",
                    "type": "ordinal",
                    "sort": ["A1", "A2", "B1", "B2"],
                    "title": "Cell",
                },
                "color": {
                    "field": "count",
                    "type": "quantitative",
                    "title": "Feasible count",
                },
                "tooltip": [
                    {"field": "cell", "type": "ordinal"},
                    {"field": "count", "type": "quantitative"},
                ],
            },
            "height": 140,
        },
        use_container_width=True,
    )
    st.caption(f"Evaluated variants: {preview['evaluated']}")


def _score_contribution_rows(rec) -> list[dict[str, float | str]]:
    feasibility_score = {
        "feasible": 1.0,
        "feasible_with_prep": 0.65,
        "not_feasible": 0.1,
    }.get(rec.feasibility.status, 0.35)
    legal_score = {
        "ok": 1.0,
        "require_check": 0.6,
        "registration": 0.5,
        "license": 0.4,
        "blocked": 0.0,
    }.get(rec.legal.legal_gate, 0.3)

    ttfm = rec.economics.time_to_first_money_days_range or [999, 999]
    speed_score = max(0.0, min(1.0, 1 - (ttfm[0] / 60)))

    net_range = rec.economics.typical_net_month_eur_range or [0, 0]
    net_mid = (net_range[0] + net_range[1]) / 2
    net_score = max(0.0, min(1.0, net_mid / 3000))

    conf = rec.economics.confidence
    conf_score = {"low": 0.35, "medium": 0.6, "high": 0.85}.get(str(conf).lower(), 0.5)

    rows = [
        {"factor": "feasibility", "value": round(feasibility_score * 100, 2)},
        {"factor": "legal", "value": round(legal_score * 100, 2)},
        {"factor": "speed", "value": round(speed_score * 100, 2)},
        {"factor": "net", "value": round(net_score * 100, 2)},
        {"factor": "confidence", "value": round(conf_score * 100, 2)},
    ]
    return rows


def run_app() -> None:
    _init_state()
    page_slugs = [slug for _, slug in NAV_ITEMS]

    params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
    if not st.session_state.get("page_initialized", False):
        st.session_state["page"] = resolve_page_from_query(
            params,
            st.session_state.get("page", "data-status"),
        )
        st.session_state["page_initialized"] = True

    if st.session_state["page"] not in page_slugs:
        st.session_state["page"] = page_slugs[0]

    inject_global_theme(st.session_state.get("theme_preset", "Light"))

    sidebar_html = """
    <div class="mm-sidebar">
      <div class="mm-sidebar-header">
        <div class="mm-sidebar-brand">
          <span class="mm-sidebar-logo">
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <defs>
                <linearGradient id="mm-logo-gradient" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#60a5fa" />
                  <stop offset="100%" stop-color="#38bdf8" />
                </linearGradient>
              </defs>
              <circle cx="12" cy="12" r="9" fill="url(#mm-logo-gradient)"></circle>
              <circle cx="12" cy="12" r="5" fill="rgba(15, 23, 42, 0.2)"></circle>
            </svg>
          </span>
          <span class="mm-sidebar-title">MoneyMap</span>
        </div>
      </div>
      <div class="mm-sidebar-divider"></div>
      <div class="mm-sidebar-section-title">Navigate</div>
    </div>
    """
    st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)
    st.sidebar.markdown('<div id="mm-nav-anchor"></div>', unsafe_allow_html=True)
    page_slug = st.sidebar.radio(
        "Navigate",
        page_slugs,
        format_func=lambda slug: NAV_LABEL_BY_SLUG.get(slug, slug),
        key="page",
        label_visibility="collapsed",
    )
    query_page = resolve_page_from_query(params, "")
    if query_page != page_slug:
        if hasattr(st, "query_params"):
            st.query_params["page"] = page_slug
        else:
            st.experimental_set_query_params(page=page_slug)
    render_view_mode_control("sidebar")

    guide_state = initialize_guide_state(st.session_state)
    mode_options = [
        copy_text("app.mode_guided", "Вести меня"),
        copy_text("app.mode_explorer", "Я сам"),
    ]
    default_mode = mode_options[0] if guide_state.get("enabled", True) else mode_options[1]
    selected_mode = st.sidebar.radio(
        copy_text("app.mode_label", "Режим работы"),
        mode_options,
        index=mode_options.index(default_mode),
        key="guide_mode_selector",
    )
    guide_state["enabled"] = selected_mode == mode_options[0]

    if guide_state["enabled"]:
        guide_layout_options = [
            copy_text("app.guide_layout_auto", "Auto"),
            copy_text("app.guide_layout_right", "Right panel"),
            copy_text("app.guide_layout_top", "Top panel"),
        ]
        st.sidebar.selectbox(
            copy_text("app.guide_layout_label", "Guide layout"),
            guide_layout_options,
            key="guide_panel_layout",
        )

    report = _get_validation()
    st.session_state["validate_report"] = report
    sync_dataset_meta(
        st.session_state,
        data_dir=st.session_state.get("data_dir", "data"),
        dataset_version=report.get("dataset_version", ""),
        reviewed_at=report.get("reviewed_at", ""),
        staleness_level=report.get("status", "WARN"),
        country="DE",
    )
    guidance_runtime = compute_guidance_runtime(
        st.session_state,
        validate_report=report,
    )
    render_header_bar(
        country=st.session_state.get("rulepack_country", "DE"),
        dataset_version=st.session_state.get("dataset_version", "unknown"),
        reviewed_at=st.session_state.get("rulepack_reviewed_at", "unknown"),
        staleness_level=st.session_state.get("staleness_level", "WARN"),
        view_mode=get_view_mode(),
    )
    if page_slug != "explore":
        st.session_state["subview"] = ""
    render_context_bar(
        page=NAV_LABEL_BY_SLUG.get(page_slug, page_slug),
        subview=st.session_state.get("subview")
        or (st.session_state.get("explore_tab") if page_slug == "explore" else None),
        selected_ids=selected_ids_from_state(st.session_state),
    )

    selected_ids = selected_ids_from_state(st.session_state)
    if guidance_runtime["is_guided"]:
        current_step = guidance_runtime["current_step"]
        primary_action = guidance_runtime["primary_action"]
        next_page = NAV_LABEL_BY_SLUG.get(
            primary_action["target_page"], primary_action["target_page"]
        )
        st.info(
            copy_text(
                "guided.next_step_banner",
                "Guided mode: следующий шаг — {title} ({page}).",
                title=str(current_step.get("title") or "Следующий шаг"),
                page=next_page,
            )
        )

        layout_label = st.session_state.get(
            "guide_panel_layout", copy_text("app.guide_layout_auto", "Auto")
        )
        use_top_layout = layout_label == copy_text("app.guide_layout_top", "Top panel")
        use_right_layout = layout_label == copy_text("app.guide_layout_right", "Right panel")
        if not use_top_layout and not use_right_layout:
            use_top_layout = page_slug in {"data-status", "profile"}
            use_right_layout = not use_top_layout

        if use_right_layout:
            guide_col, drawer_col = st.columns([0.68, 0.32])
            with guide_col:
                render_guide_panel(runtime=guidance_runtime, current_page_slug=page_slug)
            with drawer_col:
                render_detail_drawer(
                    selected_ids,
                    page_slug=page_slug,
                    expanded=bool(st.session_state.pop("open_detail_drawer", False)),
                )
        else:
            render_guide_panel(runtime=guidance_runtime, current_page_slug=page_slug)
            render_detail_drawer(
                selected_ids,
                page_slug=page_slug,
                expanded=bool(st.session_state.pop("open_detail_drawer", False)),
            )
    else:
        render_detail_drawer(
            selected_ids,
            page_slug=page_slug,
            expanded=bool(st.session_state.pop("open_detail_drawer", False)),
        )

    def _render_page_header(title: str, subtitle: str | None = None) -> None:
        header_left, header_right = st.columns([0.78, 0.22])
        with header_left:
            subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
            st.markdown(
                f"""
                <div class="mm-page-header">
                  <div>
                    <h1>{title}</h1>
                    {subtitle_html}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with header_right:
            st.markdown('<div class="mm-theme-switch">', unsafe_allow_html=True)
            st.selectbox(
                "",
                ["Light", "Dark"],
                index=(0 if st.session_state.get("theme_preset", "Light") == "Light" else 1),
                key="theme_preset",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    if page_slug == "data-status":
        st.markdown('<div class="data-status">', unsafe_allow_html=True)
        _render_page_header(
            "Data status",
            "Validation, staleness, and dataset metadata (offline-first).",
        )
        render_inline_hint(
            copy_text(
                "pages.data_status.goal_hint",
                "Проверь целостность и актуальность данных: при FATAL рекомендации и план блокируются.",
            )
        )

        def _render_status() -> None:
            with st.spinner("Loading validation snapshot..."):
                report = _get_validation()
                app_data = _get_app_data()
                pack_metrics = aggregate_pack_metrics(
                    pack_dir=Path("data/packs/de_muc"),
                    staleness_policy_days=int(report["staleness_policy_days"]),
                )
            warns_count = len(report["warns"])
            fatals_count = len(report["fatals"])
            warn_summary = _issue_summary(report["warns"])
            view_mode = get_view_mode()
            visibility = data_status_visibility(view_mode)

            status_label = report["status"].upper()

            render_kpi_grid(
                [
                    {"label": "Dataset version", "value": str(report["dataset_version"])},
                    {"label": "Reviewed at", "value": str(report["reviewed_at"])},
                    {"label": "Status", "value": status_label, "status": report["status"]},
                    {"label": "Warnings", "value": str(warns_count), "subtext": warn_summary or ""},
                    {"label": "Fatals", "value": str(fatals_count)},
                    {
                        "label": "Stale",
                        "value": str(report["stale"]),
                        "subtext": f"Staleness policy: {report['staleness_policy_days']} days",
                    },
                ]
            )

            if report["status"] == "invalid":
                st.error(
                    "**Data validation failed**\n\n"
                    "Fix FATAL issues and re-run validation. Recommendations/Plan/Export may "
                    "be unreliable until data is valid."
                )
            elif report["status"] == "stale":
                st.warning(
                    "**Data is stale**\n\n"
                    "Reviewed_at is older than staleness_policy. Show warnings and apply "
                    "cautious behavior.\n\n"
                    "For regulated domains: force legal_gate=require_check when rulepack is "
                    "stale."
                )
            else:
                st.caption("Data is valid.")

            render_info_callout(
                copy_text(
                    "pages.data_status.what_means",
                    "What this means: статус данных определяет надежность рекомендаций и доступность следующих шагов.",
                ),
                level="info",
            )

            status_controls = st.columns(2)
            with status_controls[0]:
                if st.button(
                    copy_text("pages.data_status.rerun_validate", "Re-run validate"),
                    key="data-status-rerun-validate",
                    help=action_contract_help(
                        build_action_contract(
                            label=copy_text("pages.data_status.rerun_validate", "Re-run validate"),
                            intent=copy_text(
                                "pages.data_status.rerun_intent", "Обновить validate отчет"
                            ),
                            effect=copy_text(
                                "pages.data_status.rerun_effect",
                                "Пересчитает отчет validation на текущих данных.",
                            ),
                            next_step=copy_text(
                                "pages.data_status.rerun_next", "Проверь изменившиеся WARN/FATAL"
                            ),
                            undo=copy_text(
                                "pages.data_status.rerun_undo", "Исправь данные и запусти заново"
                            ),
                        )
                    ),
                    use_container_width=True,
                ):
                    _get_validation.clear()
                    st.rerun()
            with status_controls[1]:
                blocked = fatals_count > 0
                if blocked:
                    render_info_callout(
                        copy_text(
                            "pages.data_status.continue_blocked_reason",
                            "Continue заблокирован: есть FATAL ошибки в validate report.",
                        ),
                        level="warning",
                    )
                if st.button(
                    copy_text("pages.data_status.continue_profile", "Continue → Profile"),
                    key="data-status-go-profile",
                    disabled=blocked,
                    help=action_contract_help(
                        build_action_contract(
                            label=copy_text(
                                "pages.data_status.continue_profile", "Continue → Profile"
                            ),
                            intent=copy_text(
                                "pages.data_status.continue_intent", "Перейти к заполнению профиля"
                            ),
                            effect=copy_text(
                                "pages.data_status.continue_effect",
                                "Откроет экран Profile для задания ограничений.",
                            ),
                            next_step=copy_text(
                                "pages.data_status.continue_next", "Заполни обязательные поля"
                            ),
                            undo=copy_text(
                                "pages.data_status.continue_undo",
                                "Вернись в Data status через навигацию",
                            ),
                        )
                    ),
                    use_container_width=True,
                ):
                    st.session_state["page"] = "profile"
                    st.rerun()

            if visibility["show_validate_report"]:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Validate report")
                report_json = json.dumps(report, ensure_ascii=False, indent=2, default=str)
                safe_ts = report["generated_at"].replace(":", "-")
                file_name = (
                    f"money_map_validate_report__{report['dataset_version']}__{safe_ts}.json"
                )
                st.download_button(
                    "Download validate report",
                    data=report_json,
                    file_name=file_name,
                    mime="application/json",
                )
                st.write(f"Generated at: {report['generated_at']}")
                st.write(
                    "Includes: status, fatals[], warns[], dataset_version, reviewed_at, stale, "
                    "staleness_policy_days"
                )
                if visibility["show_raw_report_json"]:
                    with st.expander("Raw report JSON"):
                        st.json(report)
                st.markdown("</div>", unsafe_allow_html=True)

            if visibility["show_validation_summary"]:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.subheader("Validation summary")

                validate_rows = build_validate_rows(report)
                severity_options = ["ALL", "FATAL", "WARN"]
                entity_options = ["ALL"] + sorted({row["entity_type"] for row in validate_rows})
                f1, f2 = st.columns(2)
                with f1:
                    severity_filter = st.selectbox(
                        "Severity filter", severity_options, key="ds-severity"
                    )
                with f2:
                    entity_filter = st.selectbox(
                        "Entity type filter", entity_options, key="ds-entity"
                    )

                filtered_rows = filter_validate_rows(
                    validate_rows,
                    severity=severity_filter,
                    entity_type=entity_filter,
                )
                if filtered_rows:
                    st.dataframe(filtered_rows, use_container_width=True)
                else:
                    st.info("No validate rows for selected filters.")

                metric_cols = st.columns(4)
                metric_cols[0].metric(
                    "Variants per cell", str(len(pack_metrics["variants_per_cell"]))
                )
                metric_cols[1].metric("Bridges", str(pack_metrics["bridges_total"]))
                metric_cols[2].metric("Routes", str(pack_metrics["routes_total"]))
                metric_cols[3].metric("Rule checks", str(pack_metrics["rule_checks_total"]))

                if pack_metrics["is_stale"]:
                    st.warning(
                        "Pack freshness warning: stale sources detected ("
                        + ", ".join(pack_metrics["stale_sources"])
                        + "). Interface remains available with cautious mode."
                    )

                c1, c2 = st.columns(2)
                with c1:
                    _render_distribution_chart(
                        "Variants by cell (core)",
                        variants_by_cell(app_data.variants, cell_resolver=_variant_cell),
                    )
                with c2:
                    _render_distribution_chart(
                        "Variants by cell (pack)",
                        pack_metrics["variants_per_cell"],
                    )

                c3, c4 = st.columns(2)
                with c3:
                    _render_distribution_chart(
                        "Variants by legal gate",
                        variants_by_legal_gate(app_data.variants),
                    )
                with c4:
                    st.markdown("**Freshness (pack files)**")
                    st.caption(f"Oldest reviewed_at: {pack_metrics['oldest_reviewed_at'] or 'n/a'}")
                    st.table(pack_metrics["freshness"])

                with st.expander("Coverage & freshness"):
                    stale_top = oldest_stale_entities(report["staleness"]["variants"], limit=10)
                    st.write(
                        "regulated domains coverage: n/a (field not present in current schema)"
                    )
                    if stale_top:
                        st.write("Oldest entities (top 10)")
                        st.table(stale_top)
                    else:
                        st.caption("No staleness age rows available.")

                if visibility["show_staleness_details"]:
                    with st.expander("Staleness details"):
                        st.write("RulePack: DE")
                        st.write(f"rulepack_reviewed_at: {app_data.rulepack.reviewed_at}")
                        st.write(f"staleness_policy_days: {report['staleness_policy_days']}")
                        rulepack_stale = report["staleness"]["rulepack"].get("is_stale")
                        st.write(f"rulepack_stale: {rulepack_stale}")
                        variant_dates = [
                            variant.review_date
                            for variant in app_data.variants
                            if variant.review_date
                        ]
                        st.write(f"variants_count: {len(app_data.variants)}")
                        if variant_dates:
                            st.write(f"oldest_variant_review_date: {min(variant_dates)}")
                            st.write(f"newest_variant_review_date: {max(variant_dates)}")
                        variants_stale = any(
                            detail.get("is_stale")
                            for detail in report["staleness"]["variants"].values()
                        )
                        st.write(f"variants_stale: {variants_stale}")
                        st.caption(
                            "If rulepack/variants are stale: show warning. For regulated domains "
                            "apply cautious behavior (force require_check)."
                        )

                if visibility["show_data_sources"]:
                    with st.expander("Data sources & diagnostics"):
                        repo_root = Path(__file__).resolve().parents[3]
                        data_dir = repo_root / "data"
                        sources = []
                        meta_path = data_dir / "meta.yaml"
                        if meta_path.exists():
                            meta_payload = read_yaml(meta_path)
                            sources.append(
                                {
                                    "Source": "data/meta.yaml",
                                    "Type": "meta",
                                    "Schema version": str(meta_payload.get("schema_version", "")),
                                    "Items": len(meta_payload),
                                }
                            )
                        rulepack_path = data_dir / "rulepacks" / "DE.yaml"
                        if rulepack_path.exists():
                            rulepack_payload = read_yaml(rulepack_path)
                            sources.append(
                                {
                                    "Source": "data/rulepacks/DE.yaml",
                                    "Type": "rulepack",
                                    "Schema version": str(
                                        rulepack_payload.get("schema_version", "")
                                    ),
                                    "Items": len(rulepack_payload.get("rules", [])),
                                }
                            )
                        variants_path = data_dir / "variants.yaml"
                        if variants_path.exists():
                            variants_payload = read_yaml(variants_path)
                            sources.append(
                                {
                                    "Source": "data/variants.yaml",
                                    "Type": "variants",
                                    "Schema version": str(
                                        variants_payload.get("schema_version", "")
                                    ),
                                    "Items": len(variants_payload.get("variants", [])),
                                }
                            )
                        if sources:
                            st.table(sources)

                        st.write(
                            "Reproducibility gate: one script/process should rebuild the same "
                            "dataset from sources."
                        )
                        st.write(
                            "Errors must be diagnosable: this page shows validation report + "
                            "sources; use the report to locate failing items."
                        )
                        st.write("CI should run: pytest + money-map validate.")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="data-status-disclaimer">', unsafe_allow_html=True)
            st.subheader("Disclaimer")
            st.write(
                "Не является: юридическим сервисом, биржей вакансий, системой прогнозирования "
                "дохода."
            )
            st.write(
                "Ограничение: не делаем юридических заключений и гарантий дохода; только "
                "диапазоны и чеклисты."
            )
            st.markdown("</div>", unsafe_allow_html=True)

        _run_with_error_boundary(_render_status)
        st.markdown("</div>", unsafe_allow_html=True)

    elif page_slug == "profile":
        _render_page_header("Profile")
        render_inline_hint(
            copy_text(
                "pages.profile.goal_hint",
                "Профиль превращает желание в ограничения: без обязательных полей рекомендации будут заблокированы.",
            )
        )

        def _render_profile() -> None:
            repo_root = Path(__file__).resolve().parents[3]
            profiles_dir = repo_root / "profiles"
            demo_profiles = sorted([path.name for path in profiles_dir.glob("*.yaml")])
            profile_loaded = False
            if demo_profiles:
                profile_choices = ["Demo profile"] + demo_profiles
                current_source = st.session_state.get("profile_source", "Demo profile")
                if current_source not in profile_choices:
                    current_source = "Demo profile"
                previous_source = st.session_state.get("profile_source")
                selected = st.selectbox(
                    "Load demo profile",
                    profile_choices,
                    index=profile_choices.index(current_source),
                    key="profile_source",
                )
                if selected != previous_source:
                    if selected != "Demo profile":
                        try:
                            st.session_state["profile"] = read_yaml(profiles_dir / selected)
                            profile_loaded = True
                        except ValueError as exc:
                            st.error(str(exc))
                    else:
                        st.session_state["profile"] = DEFAULT_PROFILE.copy()
                        profile_loaded = True

            st.caption(f"Profile source: {st.session_state['profile_source']}")
            profile = st.session_state["profile"]
            profile.setdefault("name", "")
            profile.setdefault("country", "DE")
            profile.setdefault("location", "")
            profile.setdefault("objective", "fastest_money")
            profile.setdefault("language_level", "B1")
            profile.setdefault("capital_eur", 0)
            profile.setdefault("time_per_week", 0)
            profile.setdefault("assets", [])
            profile.setdefault("skills", [])
            profile.setdefault("constraints", [])

            if profile_loaded or "profile_name" not in st.session_state:
                st.session_state["profile_name"] = profile["name"]
            if profile_loaded or "profile_country" not in st.session_state:
                st.session_state["profile_country"] = profile["country"]
            if profile_loaded or "profile_location" not in st.session_state:
                st.session_state["profile_location"] = profile["location"]
            if profile_loaded or "profile_objective" not in st.session_state:
                st.session_state["profile_objective"] = profile["objective"]
            if profile_loaded or "profile_language_level" not in st.session_state:
                st.session_state["profile_language_level"] = profile["language_level"]
            if profile_loaded or "profile_capital_eur" not in st.session_state:
                st.session_state["profile_capital_eur"] = profile["capital_eur"]
            if profile_loaded or "profile_time_per_week" not in st.session_state:
                st.session_state["profile_time_per_week"] = profile["time_per_week"]
            if profile_loaded or "profile_assets_text" not in st.session_state:
                st.session_state["profile_assets_text"] = ", ".join(profile["assets"])
            if profile_loaded or "profile_skills_text" not in st.session_state:
                st.session_state["profile_skills_text"] = ", ".join(profile["skills"])
            if profile_loaded or "profile_constraints_text" not in st.session_state:
                st.session_state["profile_constraints_text"] = ", ".join(profile["constraints"])

            left_col, right_col = st.columns([0.58, 0.42])

            with left_col:
                st.markdown("### Quick profile")
                profile["name"] = st.text_input("Name", key="profile_name")
                profile["country"] = st.selectbox("Country", ["DE"], index=0, key="profile_country")
                profile["location"] = st.text_input("Location", key="profile_location")
                objective_options = ["fastest_money", "max_net"]
                profile["objective"] = st.selectbox(
                    "Objective preset",
                    objective_options,
                    index=objective_options.index(
                        st.session_state.get("profile_objective", profile["objective"])
                    ),
                    key="profile_objective",
                )
                render_tooltip(
                    "Objective",
                    copy_text(
                        "pages.profile.objective_tooltip",
                        "Меняет приоритет ранжирования, не меняет данные.",
                    ),
                )
                profile["language_level"] = st.selectbox(
                    "Language level",
                    ["A1", "A2", "B1", "B2", "C1", "C2", "native"],
                    index=["A1", "A2", "B1", "B2", "C1", "C2", "native"].index(
                        st.session_state.get("profile_language_level", "B1")
                    ),
                    key="profile_language_level",
                )
                render_tooltip(
                    "Language level",
                    copy_text(
                        "pages.profile.language_tooltip",
                        "Влияет на доступные варианты и скорость входа.",
                    ),
                )
                profile["time_per_week"] = st.slider(
                    "Time per week",
                    min_value=0,
                    max_value=60,
                    value=int(
                        st.session_state.get("profile_time_per_week", profile["time_per_week"])
                    ),
                    key="profile_time_per_week",
                )
                render_tooltip(
                    "Time per week",
                    copy_text(
                        "pages.profile.time_tooltip", "Реально доступные часы в неделю для старта."
                    ),
                )
                profile["capital_eur"] = st.number_input(
                    "Capital (EUR)",
                    min_value=0,
                    value=st.session_state.get("profile_capital_eur", profile["capital_eur"]),
                    key="profile_capital_eur",
                )
                render_tooltip(
                    "Capital",
                    copy_text(
                        "pages.profile.capital_tooltip",
                        "Сумма, которую можно вложить без критичного риска.",
                    ),
                )
                st.caption(f"Capital band: {_capital_band(int(profile['capital_eur']))}")

                assets_text = st.text_input("Assets (comma separated)", key="profile_assets_text")
                skills_text = st.text_input("Skills (comma separated)", key="profile_skills_text")
                constraints_text = st.text_area(
                    "Constraints (comma separated)", key="profile_constraints_text"
                )
                render_tooltip(
                    "Constraints",
                    copy_text(
                        "pages.profile.constraints_tooltip",
                        "Ограничения применяются как фильтры и их можно ослабить позже.",
                    ),
                )
                profile["assets"] = [
                    item.strip() for item in assets_text.split(",") if item.strip()
                ]
                profile["skills"] = [
                    item.strip() for item in skills_text.split(",") if item.strip()
                ]
                profile["constraints"] = [
                    item.strip() for item in constraints_text.split(",") if item.strip()
                ]

            st.session_state["profile"] = profile
            _sync_profile_session_state(profile)
            profile_validation = validate_profile(profile)

            with right_col:
                if profile_validation["is_ready"]:
                    with st.spinner("Updating preview..."):
                        preview = _profile_preview_snapshot(profile)
                    _render_profile_preview(preview)
                else:
                    st.info(
                        copy_text(
                            "pages.profile.preview_locked",
                            "Complete required profile fields to unlock live preview.",
                        )
                    )

                if profile_validation["missing"]:
                    st.info(
                        copy_text(
                            "pages.profile.missing_required_prefix", "Missing required fields: "
                        )
                        + ", ".join(profile_validation["missing"])
                    )
                for warning in profile_validation["warnings"]:
                    st.warning(warning)

                st.caption(f"Profile hash: {st.session_state.get('profile_hash', '')}")
                if profile_validation["is_ready"]:
                    st.success("Profile ready")
                else:
                    st.caption("Profile draft")
                    if profile_validation["missing"]:
                        render_info_callout(
                            copy_text(
                                "pages.profile.blocked_reason",
                                "Почему заблокировано: не заполнены обязательные поля.",
                            ),
                            level="warning",
                        )
                        for field_name in profile_validation["missing"]:
                            st.caption(
                                f"• {copy_text('pages.profile.todo_prefix', 'Что сделать: заполнить поле')} `{field_name}`"
                            )

                if st.button(
                    "Go to Recommendations",
                    key="profile-go-recommendations",
                    disabled=not profile_validation["is_ready"],
                    help=action_contract_help(
                        build_action_contract(
                            label="Go to Recommendations",
                            intent=copy_text(
                                "pages.profile.continue_intent", "Перейти к выбору варианта"
                            ),
                            effect=copy_text(
                                "pages.profile.continue_effect",
                                "Откроет Recommendations с текущим профилем.",
                            ),
                            next_step=copy_text(
                                "pages.profile.continue_next",
                                "Проверь Reality Check и выбери вариант",
                            ),
                            undo=copy_text(
                                "pages.profile.continue_undo",
                                "Вернись в Profile и отредактируй поля",
                            ),
                        )
                    ),
                ):
                    st.session_state["page"] = "recommendations"
                    st.rerun()

        _run_with_error_boundary(_render_profile)

    elif page_slug == "jobs-live":
        _render_page_header("Jobs (Live)", "Vacancies with automatic live/cache/seed fallback.")

        def _render_jobs_live() -> None:
            profile = st.session_state.get("profile", {})
            default_city = str(profile.get("location", "Munich") or "Munich")
            default_profile_query = (
                ", ".join(profile.get("skills", []))
                if isinstance(profile.get("skills"), list)
                else ""
            )
            default_profile_query = default_profile_query or str(profile.get("objective", ""))

            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                city = st.text_input("Город", value=default_city, key="jobs_city")
            with c2:
                radius_km = st.number_input(
                    "Радиус (км)", min_value=1, max_value=200, value=25, key="jobs_radius"
                )
            with c3:
                days = st.number_input("Дни", min_value=1, max_value=30, value=7, key="jobs_days")
            with c4:
                size = st.number_input(
                    "Размер выдачи", min_value=1, max_value=100, value=20, key="jobs_size"
                )
            with c5:
                profile_query = st.text_input(
                    "Профиль", value=default_profile_query, key="jobs_profile"
                )

            rows, source_meta = resolve_jobs_source(
                city=city,
                radius_km=int(radius_km),
                days=int(days),
                size=int(size),
                profile=profile_query,
            )
            st.session_state["jobs_last_source"] = source_meta

            source = source_meta.get("source", "unknown")
            snapshot = source_meta.get("snapshot", "")
            if source == "live":
                st.success("Источник данных: live")
            elif source == "cache":
                st.warning(f"Источник данных: cache · snapshot: {snapshot}")
            else:
                st.info("Источник данных: seed (компактный fallback)")

            table_rows = []
            for row in rows:
                table_rows.append(
                    {
                        "title": row.get("title", ""),
                        "company": row.get("company", ""),
                        "city": row.get("city", ""),
                        "publishedAt": row.get("publishedAt", ""),
                        "refnr": row.get("refnr", ""),
                        "url": row.get("url", ""),
                    }
                )
            st.dataframe(table_rows, use_container_width=True, hide_index=True)

            st.markdown("### Create Variant Draft")
            if rows:
                options = {
                    " · ".join(
                        [
                            str(row.get("title", "")),
                            str(row.get("company", "")),
                            str(row.get("city", "")),
                        ]
                    ): idx
                    for idx, row in enumerate(rows)
                }
                selected_label = st.selectbox(
                    "Vacancy", list(options.keys()), key="jobs_selected_row"
                )
                selected_row = rows[options[selected_label]]
                if st.button("Create Variant Draft", key="jobs_create_variant_draft"):
                    draft = create_variant_draft(selected_row)
                    drafts = st.session_state.get("jobs_variant_drafts", [])
                    drafts.insert(0, draft)
                    st.session_state["jobs_variant_drafts"] = drafts[:20]
                    st.success(f"Draft created: {draft['variant_id']}")

            drafts = st.session_state.get("jobs_variant_drafts", [])
            if drafts:
                with st.expander("Drafts", expanded=False):
                    st.json(drafts)

        _run_with_error_boundary(_render_jobs_live)

    elif page_slug == "explore":
        _render_page_header("Explore", "Browse matrix/taxonomy/bridges (offline, deterministic).")

        def _render_explore() -> None:
            report = _get_validation()
            if report["fatals"]:
                _render_status(
                    "invalid_data",
                    "Explore is blocked by validation fatals.",
                    reasons=[", ".join(_issue_codes(report["fatals"]))],
                    level="error",
                )
                return

            if report["status"] == "stale":
                _render_status(
                    "stale_warning",
                    "Data is stale. Legal hints should be treated cautiously.",
                    reasons=["Rulepack/variant freshness exceeded staleness policy."],
                    level="warning",
                )

            tab_options = ["Matrix", "Taxonomy", "Bridges", "Paths", "Variants Library"]
            selected_tab = st.radio("Explore tabs", tab_options, key="explore_tab", horizontal=True)
            st.session_state["subview"] = selected_tab.lower()

            with st.spinner("Building explore view..."):
                app_data = _get_app_data()
                variants = sorted(app_data.variants, key=_stable_variant_sort_key)

            _render_status("ready", f"Explore tab ready: {selected_tab}.")
            render_inline_hint(
                copy_text(
                    "pages.explore.goal_hint",
                    "Explore показывает карту связей: ячейки, механизмы, мосты и примеры.",
                )
            )

            if selected_tab == "Matrix":
                render_inline_hint(
                    copy_text(
                        "pages.explore.matrix_hint",
                        "Нажми ячейку, чтобы увидеть варианты и быстро отправить фильтр в Recommendations.",
                    )
                )
                selected_cell = st.selectbox("Cell", CELL_OPTIONS, key="explore_selected_cell")
                st.session_state["selected_cell_id"] = selected_cell
                cell_variants = [v for v in variants if _variant_cell(v) == selected_cell]

                matrix_rows = []
                for cell in CELL_OPTIONS:
                    variants_in_cell = [v for v in variants if _variant_cell(v) == cell]
                    feasible_count = sum(
                        1
                        for variant in variants_in_cell
                        if not any(
                            "blocked" in str(item).lower() for item in variant.legal.values()
                        )
                    )
                    matrix_rows.append(
                        {
                            "cell": cell,
                            "variants": len(variants_in_cell),
                            "feasible_now": feasible_count,
                        }
                    )
                st.dataframe(matrix_rows, use_container_width=True)

                if st.button("Filter Recommendations to this cell", key="explore-cell-to-rec"):
                    st.session_state["filters"]["include_cells"] = [selected_cell]
                    st.session_state["page"] = "recommendations"
                    st.rerun()

                st.subheader(f"Cell {selected_cell}")
                if not cell_variants:
                    _render_status(
                        "empty_view",
                        "No variants for selected cell.",
                        reasons=["Try another cell or open Bridges tab."],
                        level="warning",
                    )
                    return
                st.write("Typical variants:")
                for variant in cell_variants[:12]:
                    _render_explore_variant_card(
                        variant,
                        taxonomy=_variant_taxonomy(variant),
                        cell=selected_cell,
                        stale=is_variant_stale(variant, app_data.meta.staleness_policy),
                    )

            elif selected_tab == "Taxonomy":
                render_inline_hint(
                    copy_text(
                        "pages.explore.taxonomy_hint",
                        "Выбери механизм и изучи связи taxonomy → cell → variant.",
                    )
                )
                selected_taxonomy = st.selectbox(
                    "Taxonomy",
                    TAXONOMY_OPTIONS,
                    key="explore_selected_taxonomy",
                )
                st.session_state["selected_taxonomy_id"] = selected_taxonomy
                tax_variants = [v for v in variants if _variant_taxonomy(v) == selected_taxonomy]

                dot_lines = [
                    "digraph taxonomy {",
                    "rankdir=LR;",
                    f'"{selected_taxonomy}" [shape=box, style=filled, fillcolor="#dbeafe"];',
                ]
                nodes = [{"id": selected_taxonomy, "type": "taxonomy"}]
                edges = []
                for cell in sorted({_variant_cell(v) for v in tax_variants}):
                    dot_lines.append(f'"{selected_taxonomy}" -> "{cell}";')
                    nodes.append({"id": cell, "type": "cell"})
                    edges.append(
                        {
                            "id": f"{selected_taxonomy}->{cell}",
                            "from": selected_taxonomy,
                            "to": cell,
                        }
                    )
                for variant in tax_variants[:8]:
                    vid = variant.variant_id
                    c = _variant_cell(variant)
                    dot_lines.append(f'"{c}" -> "{vid}";')
                    nodes.append({"id": vid, "type": "variant"})
                    edges.append({"id": f"{c}->{vid}", "from": c, "to": vid})
                dot_lines.append("}")

                render_graph_fallback(
                    title="Taxonomy graph",
                    graphviz_dot="\n".join(dot_lines),
                    nodes_rows=nodes,
                    edges_rows=edges,
                    key_prefix="taxonomy",
                    interactive_available=False,
                )

                if st.button("Filter Recommendations by this taxonomy", key="explore-tax-to-rec"):
                    st.session_state["filters"]["include_taxonomy"] = [selected_taxonomy]
                    st.session_state["page"] = "recommendations"
                    st.rerun()

                st.subheader(f"Taxonomy: {selected_taxonomy}")
                if not tax_variants:
                    _render_status(
                        "empty_view",
                        "No variants for selected taxonomy.",
                        reasons=["Try another taxonomy category."],
                        level="warning",
                    )
                    return
                st.write("Examples:")
                for variant in tax_variants[:10]:
                    _render_explore_variant_card(
                        variant,
                        taxonomy=selected_taxonomy,
                        cell=_variant_cell(variant),
                        stale=is_variant_stale(variant, app_data.meta.staleness_policy),
                    )

            elif selected_tab == "Bridges":
                render_inline_hint(
                    copy_text(
                        "pages.explore.bridges_hint",
                        "Мост показывает переход между ячейками и связанные варианты.",
                    )
                )
                selected_bridge = st.selectbox(
                    "Bridge",
                    BRIDGE_OPTIONS,
                    key="explore_selected_bridge",
                )
                st.session_state["selected_bridge_id"] = selected_bridge
                frm, to = selected_bridge.split("->", 1)
                bridge_variants = [v for v in variants if _variant_cell(v) in {frm, to}]

                dot = "\n".join(
                    [
                        "digraph bridges {",
                        "rankdir=LR;",
                        '"A1" -> "A2" [label="standardize"];',
                        '"A2" -> "B2" [label="delegate"];',
                        '"A1" -> "B1" [label="formalize"];',
                        '"B1" -> "B2" [label="systemize"];',
                        "}",
                    ]
                )
                nodes = [{"id": c, "type": "cell"} for c in CELL_OPTIONS]
                edges = [
                    {"id": b, "from": b.split("->", 1)[0], "to": b.split("->", 1)[1]}
                    for b in BRIDGE_OPTIONS
                ]
                render_graph_fallback(
                    title="Bridges directed graph",
                    graphviz_dot=dot,
                    nodes_rows=nodes,
                    edges_rows=edges,
                    key_prefix="bridges",
                    interactive_available=False,
                )

                st.subheader(f"Bridge {frm} → {to}")
                st.write("Preconditions:")
                st.write("- Validate feasibility blockers")
                st.write("- Check legal gate for regulated domains")
                st.write("Steps:")
                st.write("- Prepare minimal artifacts")
                st.write("- Run recommendations with updated objective")
                if st.button("Use bridge as filter", key="explore-bridge-to-rec"):
                    st.session_state["filters"]["include_cells"] = [frm, to]
                    st.session_state["page"] = "recommendations"
                    st.rerun()
                if not bridge_variants:
                    _render_status(
                        "empty_view",
                        "No variants mapped to this bridge yet.",
                        reasons=["Use neighboring bridge or relax filters in Recommendations."],
                        level="warning",
                    )
                    return
                st.write("Common variants for this bridge:")
                for variant in bridge_variants[:10]:
                    _render_explore_variant_card(
                        variant,
                        taxonomy=_variant_taxonomy(variant),
                        cell=_variant_cell(variant),
                        stale=is_variant_stale(variant, app_data.meta.staleness_policy),
                    )

            elif selected_tab == "Paths":
                render_inline_hint(
                    copy_text(
                        "pages.explore.paths_hint",
                        "Маршрут — это цепочка переходов. Можно использовать как плановый backbone.",
                    )
                )
                path_options = {
                    "Route-1": ["A1", "A2", "B2"],
                    "Route-2": ["A1", "B1", "B2"],
                    "Route-3": ["A2", "B2"],
                }
                selected_path = st.selectbox("Route", list(path_options.keys()), key="explore-path")
                st.session_state["selected_path_id"] = selected_path
                cells = path_options[selected_path]
                st.write("Path card:", " → ".join(cells))
                dot_lines = ["digraph route {", "rankdir=LR;"]
                for a, b in zip(cells, cells[1:]):
                    dot_lines.append(f'"{a}" -> "{b}";')
                dot_lines.append("}")
                render_graph_fallback(
                    title="Route diagram",
                    graphviz_dot="\n".join(dot_lines),
                    nodes_rows=[{"id": c, "type": "cell"} for c in cells],
                    edges_rows=[
                        {"id": f"{a}->{b}", "from": a, "to": b} for a, b in zip(cells, cells[1:])
                    ],
                    key_prefix="paths",
                    interactive_available=False,
                )
                if st.button("Use as plan backbone", key="explore-path-to-rec"):
                    st.session_state["filters"]["include_cells"] = cells
                    st.session_state["page"] = "recommendations"
                    st.rerun()

            elif selected_tab == "Variants Library":
                render_inline_hint(
                    copy_text(
                        "pages.explore.library_hint",
                        "Каталог примеров без ранжирования. Фильтруй и отправляй в Recommendations.",
                    )
                )
                selected_cell_filter = st.multiselect(
                    "Cell",
                    CELL_OPTIONS,
                    default=st.session_state["filters"].get("include_cells", []),
                )
                selected_tax_filter = st.multiselect(
                    "Taxonomy",
                    TAXONOMY_OPTIONS,
                    default=st.session_state["filters"].get("include_taxonomy", []),
                )
                max_ttfm = st.slider("Max TTFM days", 1, 120, 60)

                filtered = []
                for variant in variants:
                    cell = _variant_cell(variant)
                    taxonomy = _variant_taxonomy(variant)
                    ttfm = variant.economics.get("time_to_first_money_days_range") or [999, 999]
                    if selected_cell_filter and cell not in selected_cell_filter:
                        continue
                    if selected_tax_filter and taxonomy not in selected_tax_filter:
                        continue
                    if ttfm and ttfm[0] > max_ttfm:
                        continue
                    filtered.append((variant, cell, taxonomy))

                st.caption(f"Results: {len(filtered)}")
                for variant, cell, taxonomy in filtered[:30]:
                    col_l, col_r = st.columns([0.78, 0.22])
                    with col_l:
                        st.markdown(
                            f"**{variant.title}** · `{variant.variant_id}` · {cell} / {taxonomy}"
                        )
                    with col_r:
                        if st.button("Send to Rec", key=f"lib-send-{variant.variant_id}"):
                            st.session_state["selected_variant_id"] = variant.variant_id
                            st.session_state["selected_cell_id"] = cell
                            st.session_state["selected_taxonomy_id"] = taxonomy
                            st.session_state["filters"]["include_cells"] = [cell]
                            st.session_state["filters"]["include_taxonomy"] = [taxonomy]
                            st.session_state["page"] = "recommendations"
                            st.rerun()

                if not filtered:
                    st.info("No variants for current library filters.")

        _run_with_error_boundary(_render_explore)

    elif page_slug == "classify":
        _render_page_header("Classify", "Classify idea text into taxonomy + matrix cell.")

        def _render_classify() -> None:
            report = _get_validation()
            if report["fatals"]:
                _render_status(
                    "error",
                    "Classify is blocked by validation fatals.",
                    reasons=[", ".join(_issue_codes(report["fatals"]))],
                    level="error",
                )
                return

            if report["status"] == "stale":
                _render_status(
                    "stale_warning",
                    "Data is stale. Classification legal hints are conservative.",
                    reasons=["Rulepack/variant freshness exceeded staleness policy."],
                    level="warning",
                )

            idea_text = st.text_area(
                "Idea text",
                key="classify_idea_text",
                placeholder="Describe your idea in 1-5 sentences...",
            )

            if len(idea_text.strip()) < 8:
                _render_status(
                    "draft",
                    "Add at least one short sentence to classify.",
                    reasons=["Current input is too short for reliable signals."],
                )
                return

            run_clicked = st.button("Classify")
            if run_clicked:
                st.session_state["classify_error"] = ""
                with st.spinner("Classifying idea..."):
                    _render_status("loading", "Running deterministic classification pipeline...")
                    try:
                        st.session_state["classify_result"] = classify_idea_text(
                            idea_text,
                            app_data=_get_app_data(),
                            data_dir="data",
                        )
                    except Exception as exc:  # noqa: BLE001
                        st.session_state["classify_error"] = str(exc)
                        st.session_state["classify_result"] = None

            if st.session_state.get("classify_error"):
                _render_status(
                    "error",
                    "Classification failed.",
                    reasons=[st.session_state["classify_error"]],
                    level="error",
                )
                return

            result = st.session_state.get("classify_result")
            if result is None:
                return

            status = "ambiguous" if result.ambiguity == "ambiguous" else "results"
            level = "warning" if status == "ambiguous" else "info"
            _render_status(
                status,
                f"Top cell guess: {result.cell_guess} (confidence={result.confidence:.2f})",
                reasons=result.reasons[:3],
                level=level,
            )

            st.subheader("Top-3 taxonomy candidates")
            for idx, candidate in enumerate(result.top3, start=1):
                st.markdown(
                    f"**{idx}. {candidate.taxonomy_label} ({candidate.taxonomy_id})** · "
                    f"Cell: {candidate.cell_guess} · Score: {candidate.score:.2f}"
                )
                if candidate.reasons:
                    st.caption("Why: " + "; ".join(candidate.reasons[:3]))

                samples = candidate.sample_variants[:5]
                if samples:
                    st.markdown("Mini-Variant Cards")
                for sample in samples:
                    with st.container():
                        st.markdown(f"**{sample.title}** · `{sample.variant_id}`")
                        st.caption(
                            f"taxonomy={sample.taxonomy_id} · cell={sample.cell} · "
                            f"feasibility={sample.feasibility_status}"
                        )
                        st.write(
                            "TTFM: "
                            + (
                                "-".join(map(str, sample.time_to_first_money_days_range))
                                if sample.time_to_first_money_days_range
                                else "unknown"
                            )
                        )
                        st.write(
                            "Net/month: €"
                            + (
                                "-".join(map(str, sample.typical_net_month_eur_range))
                                if sample.typical_net_month_eur_range
                                else "unknown"
                            )
                        )
                        st.write(f"Legal gate: {sample.legal.gate}")

                        c1, c2, c3 = st.columns(3)
                        if c1.button(
                            "Open in Explore",
                            key=f"classify-explore-{idx}-{sample.variant_id}",
                        ):
                            st.session_state["explore_tab"] = "Taxonomy"
                            st.session_state["explore_selected_taxonomy"] = candidate.taxonomy_id
                            st.session_state["explore_selected_cell"] = candidate.cell_guess
                            st.session_state["page"] = "explore"
                            st.rerun()

                        if c2.button(
                            "Open in Recommendations",
                            key=f"classify-reco-{idx}-{sample.variant_id}",
                        ):
                            st.session_state["classify_prefilter"] = {
                                "taxonomy_id": candidate.taxonomy_id,
                                "cell": candidate.cell_guess,
                                "from_classify": True,
                            }
                            st.session_state["selected_variant_id"] = sample.variant_id
                            st.session_state["page"] = "recommendations"
                            st.rerun()

                        if c3.button(
                            "Select for Plan",
                            key=f"classify-plan-select-{idx}-{sample.variant_id}",
                        ):
                            st.session_state["classify_selected_variant_id"] = sample.variant_id
                            st.session_state["selected_variant_id"] = sample.variant_id

            selected_for_plan = st.session_state.get("classify_selected_variant_id", "")
            st.caption(
                "Selected for Plan: " + (f"`{selected_for_plan}`" if selected_for_plan else "none")
            )
            if st.button(
                "Go to Plan",
                disabled=not bool(selected_for_plan),
                key="classify-go-plan",
            ):
                st.session_state["page"] = "plan"
                st.rerun()

        _run_with_error_boundary(_render_classify)

    elif page_slug == "recommendations":
        _render_page_header("Recommendations")

        def _render_recommendations() -> None:
            report = _get_validation()
            _guard_fatals(report)
            profile = st.session_state["profile"]
            classify_prefilter = st.session_state.get("classify_prefilter") or {}
            if classify_prefilter.get("from_classify"):
                st.info(
                    "Opened from Classify: "
                    f"taxonomy={classify_prefilter.get('taxonomy_id')} | "
                    f"cell={classify_prefilter.get('cell')}"
                )

            profile_validation = validate_profile(profile)
            if not profile_validation["is_ready"]:
                reasons = []
                if profile_validation["missing"]:
                    reasons.append("Missing: " + ", ".join(profile_validation["missing"]))
                reasons.extend(
                    [f"Warning: {warning}" for warning in profile_validation["warnings"]]
                )
                _render_status(
                    "not_ready",
                    copy_text(
                        "pages.recommendations.not_ready",
                        "Profile is not ready for recommendations.",
                    ),
                    reasons=reasons,
                    level="warning",
                )
                return

            st.markdown("### Top controls")
            render_inline_hint(
                copy_text(
                    "pages.recommendations.top_hint", "Настрой фильтры и пересчитай рекомендации."
                )
            )
            render_tooltip(
                "Objective",
                copy_text(
                    "pages.recommendations.objective_hint",
                    "Меняет веса ранжирования. Данные не изменяются.",
                ),
            )
            render_tooltip(
                "Filters",
                copy_text(
                    "pages.recommendations.filters_hint",
                    "Фильтры отсекают варианты. Если пусто — ослабь ограничения.",
                ),
            )
            top_bar = st.columns([0.26, 0.20, 0.18, 0.18, 0.18])
            objective_options = ["fastest_money", "max_net"]
            current_objective = _ensure_objective(profile, objective_options)
            with top_bar[0]:
                selected_objective = st.selectbox(
                    "Objective",
                    objective_options,
                    index=objective_options.index(
                        st.session_state.get("rec_objective", current_objective)
                    ),
                    key="rec_objective",
                )
            with top_bar[1]:
                top_n = st.slider(
                    "Top N",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.get("rec_top_n", 10),
                    key="rec_top_n",
                )
            with top_bar[2]:
                start2w = st.checkbox("Startable ≤ 2 weeks", key="rec_qf_start2w")
            with top_bar[3]:
                low_legal = st.checkbox("Low legal friction", key="rec_qf_low_legal")
            with top_bar[4]:
                max_risk_low = st.checkbox("Max risk: low", key="rec_qf_low_risk")

            profile["objective"] = selected_objective
            st.session_state["profile"] = profile
            _sync_profile_session_state(profile)

            max_time_default = (
                14
                if start2w
                else int(st.session_state["filters"].get("max_time_to_money_days", 60))
            )
            st.session_state["filters"]["max_time_to_money_days"] = int(
                st.number_input(
                    "Max time to first money (days)",
                    value=max_time_default,
                    key="rec_max_time_to_money_days",
                )
            )
            st.session_state["filters"]["exclude_blocked"] = bool(
                st.checkbox(
                    "Exclude blocked",
                    value=bool(
                        st.session_state["filters"].get("exclude_blocked", True) or low_legal
                    ),
                    key="rec_exclude_blocked",
                )
            )
            st.session_state["filters"]["exclude_not_feasible"] = bool(
                st.checkbox(
                    "Exclude not feasible",
                    value=bool(
                        st.session_state["filters"].get("exclude_not_feasible", False)
                        or max_risk_low
                    ),
                    key="rec_exclude_not_feasible",
                )
            )
            st.session_state["filters"]["top_n"] = int(top_n)
            sync_filters_and_objective(
                st.session_state,
                filters=st.session_state["filters"],
                objective_preset=selected_objective,
            )

            active_filter_chips = {
                "objective": selected_objective,
                "top_n": str(top_n),
                "max_time_days": str(st.session_state["filters"].get("max_time_to_money_days", 60)),
                "exclude_blocked": str(st.session_state["filters"].get("exclude_blocked", True)),
                "exclude_not_feasible": str(
                    st.session_state["filters"].get("exclude_not_feasible", False)
                ),
            }
            chip_action = render_filter_chips_bar(
                active_filters=active_filter_chips, key_prefix="rec-filters"
            )
            if chip_action == "__reset__":
                st.session_state["filters"] = DEFAULT_FILTERS.copy()
                st.rerun()
            if chip_action == "exclude_blocked":
                st.session_state["filters"]["exclude_blocked"] = False
                st.rerun()
            if chip_action == "exclude_not_feasible":
                st.session_state["filters"]["exclude_not_feasible"] = False
                st.rerun()
            if chip_action == "max_time_days":
                st.session_state["filters"]["max_time_to_money_days"] = 60
                st.rerun()

            def _run_recommendations() -> None:
                result = _get_recommendations(
                    json.dumps(profile, ensure_ascii=False),
                    st.session_state.get("objective_preset", profile["objective"]),
                    st.session_state["filters"],
                    top_n,
                )
                st.session_state["last_recommendations"] = result
                st.session_state["recommendations"] = result
                st.session_state["recommend_diagnostics"] = result.diagnostics
                ranked_ids = {item.variant.variant_id for item in result.ranked_variants}
                selected = st.session_state.get("selected_variant_id")
                if selected and selected not in ranked_ids:
                    st.session_state["selected_variant_id"] = ""
                    st.session_state["plan"] = None

            render_tooltip(
                "Recompute",
                copy_text(
                    "pages.recommendations.recompute_tooltip",
                    "Пересчитает Top-N по текущим фильтрам.",
                ),
            )
            if st.button(
                "Recompute",
                key="recompute-recommendations",
                help=action_contract_help(
                    build_action_contract(
                        label="Recompute",
                        intent=copy_text(
                            "pages.recommendations.recompute_intent", "Обновить ранжирование"
                        ),
                        effect=copy_text(
                            "pages.recommendations.recompute_effect",
                            "Пересчитает результаты с текущими фильтрами.",
                        ),
                        next_step=copy_text(
                            "pages.recommendations.recompute_next", "Проверь обновлённые карточки"
                        ),
                        undo=copy_text(
                            "pages.recommendations.recompute_undo",
                            "Сними фильтры или измени objective",
                        ),
                    )
                ),
            ):
                _run_recommendations()

            result = st.session_state.get("recommendations") or st.session_state.get(
                "last_recommendations"
            )
            if result is None:
                _render_status(
                    "not_ready",
                    "Run recommendations to see results.",
                    reasons=["No recommendations have been generated yet."],
                )
                return

            st.markdown("### Reality Check")
            render_info_callout(
                copy_text(
                    "pages.recommendations.reality_hint", "Проверь ключевые блокеры и quick fixes."
                ),
                level="info",
            )
            blocker_counts = Counter()
            for rec in result.ranked_variants:
                blocker_counts.update(rec.feasibility.blockers)
            top_blockers = blocker_counts.most_common(3)
            if top_blockers:
                for blocker, cnt in top_blockers:
                    st.warning(
                        f"Blocker: {blocker} · impact: {cnt} variants · quick fix: adjust filters"
                    )
            else:
                st.caption("No major blockers in current top results.")

            qf1, qf2, qf3 = st.columns(3)
            if qf1.button("Quick fix: allow prep", key="rc-allow-prep"):
                st.session_state["filters"]["exclude_not_feasible"] = False
                _run_recommendations()
            if qf2.button("Quick fix: relax legal", key="rc-relax-legal"):
                st.session_state["filters"]["exclude_blocked"] = False
                _run_recommendations()
            if qf3.button("Quick fix: extend time", key="rc-extend-time"):
                st.session_state["filters"]["max_time_to_money_days"] = 60
                _run_recommendations()

            if not result.ranked_variants:
                diagnostics = []
                if result.diagnostics.get("reasons"):
                    diagnostics = [
                        f"{reason}: {count}"
                        for reason, count in result.diagnostics["reasons"].items()
                    ]
                empty_action = render_empty_state(
                    title=copy_text("pages.recommendations.empty_title", "Ничего не найдено"),
                    reason=copy_text(
                        "pages.recommendations.empty_reason",
                        "Все варианты были отфильтрованы текущими ограничениями.",
                    ),
                    actions=[
                        {"key": "allow_prep", "label": "Quick fix: allow prep"},
                        {"key": "relax_legal", "label": "Quick fix: relax legal"},
                        {"key": "extend_time", "label": "Quick fix: extend time"},
                    ],
                    diagnostics=diagnostics,
                    key_prefix="rec-empty",
                )
                if empty_action == "allow_prep":
                    st.session_state["filters"]["exclude_not_feasible"] = False
                    _run_recommendations()
                elif empty_action == "relax_legal":
                    st.session_state["filters"]["exclude_blocked"] = False
                    _run_recommendations()
                elif empty_action == "extend_time":
                    st.session_state["filters"]["max_time_to_money_days"] = 60
                    _run_recommendations()
                return

            mode = st.radio(
                "Results mode", ["Cards", "Table"], horizontal=True, key="rec-view-mode"
            )

            if mode == "Table":
                rows = []
                for rec in result.ranked_variants:
                    rows.append(
                        {
                            "score": round(rec.score, 4),
                            "title": rec.variant.title,
                            "variant_id": rec.variant.variant_id,
                            "time_to_first_money": "-".join(
                                map(str, rec.economics.time_to_first_money_days_range)
                            ),
                            "net_range": "€"
                            + "-".join(map(str, rec.economics.typical_net_month_eur_range)),
                            "feasibility": rec.feasibility.status,
                            "legal_gate": rec.legal.legal_gate,
                            "confidence": rec.economics.confidence,
                            "cell": _variant_cell(rec.variant),
                            "taxonomy": _variant_taxonomy(rec.variant),
                        }
                    )
                st.dataframe(rows, use_container_width=True)
                selected_table_variant = st.selectbox(
                    "Select variant",
                    [""] + [row["variant_id"] for row in rows],
                    key="rec-table-select",
                    format_func=lambda val: val or "none",
                )
                if selected_table_variant and st.button(
                    "Select & Build Plan", key="rec-table-build"
                ):
                    st.session_state["selected_variant_id"] = selected_table_variant
                    st.session_state["page"] = "plan"
                    st.rerun()
                return

            for rec in result.ranked_variants:
                with st.container():
                    stale_label = " (stale)" if rec.stale else ""
                    st.subheader(rec.variant.title)
                    st.caption(f"ID: {rec.variant.variant_id}{stale_label}")
                    render_badge_set(
                        feasibility=rec.feasibility.status,
                        legal_gate=rec.legal.legal_gate,
                        staleness="warn" if rec.stale else "ok",
                        confidence=rec.economics.confidence,
                    )

                    st.write("**Summary:** " + rec.variant.title)
                    st.write(
                        f"**Cell/Taxonomy:** `{_variant_cell(rec.variant)}` / `{_variant_taxonomy(rec.variant)}`"
                    )

                    st.markdown("**Feasibility**")
                    st.write(f"Status: {rec.feasibility.status}")
                    if rec.feasibility.blockers:
                        st.write("Blockers: " + "; ".join(rec.feasibility.blockers[:3]))
                    if rec.feasibility.prep_steps:
                        st.write("Prep steps: " + "; ".join(rec.feasibility.prep_steps[:3]))

                    st.markdown("**Economics**")
                    st.write(
                        "TTFM: "
                        + "-".join(map(str, rec.economics.time_to_first_money_days_range))
                        + " days; net/month: €"
                        + "-".join(map(str, rec.economics.typical_net_month_eur_range))
                        + f"; confidence: {rec.economics.confidence}"
                    )

                    st.markdown("**Legal / Compliance**")
                    st.write(f"Legal gate: {rec.legal.legal_gate}")
                    if rec.legal.checklist:
                        st.write("Checklist: " + "; ".join(rec.legal.checklist[:3]))

                    st.markdown("**Почему в топе**")
                    for item in rec.pros[:3]:
                        st.write(f"- {item}")

                    st.markdown("**Что мешает**")
                    for item in rec.cons[:2]:
                        st.write(f"- {item}")

                    with st.expander("Explain score"):
                        rows = _score_contribution_rows(rec)
                        st.vega_lite_chart(
                            {
                                "data": {"values": rows},
                                "mark": "bar",
                                "encoding": {
                                    "x": {"field": "factor", "type": "nominal", "title": "Factor"},
                                    "y": {
                                        "field": "value",
                                        "type": "quantitative",
                                        "title": "Contribution",
                                    },
                                    "tooltip": [
                                        {"field": "factor", "type": "nominal"},
                                        {"field": "value", "type": "quantitative"},
                                    ],
                                },
                                "height": 180,
                            },
                            use_container_width=True,
                        )

                    c1, c2, c3 = st.columns(3)
                    if c1.button(
                        f"Select & Build Plan · {rec.variant.variant_id}",
                        key=f"rec-plan-{rec.variant.variant_id}",
                        help=action_contract_help(
                            build_action_contract(
                                label="Select & Build Plan",
                                intent=copy_text(
                                    "pages.recommendations.select_intent",
                                    "Сохранить вариант и перейти к плану",
                                ),
                                effect=copy_text(
                                    "pages.recommendations.select_effect",
                                    "Обновит Selected в контексте и откроет Plan.",
                                ),
                                next_step=copy_text(
                                    "pages.recommendations.select_next",
                                    "Проверь Checklist / 4 weeks / Compliance",
                                ),
                                undo=copy_text(
                                    "pages.recommendations.select_undo",
                                    "Выбери другой вариант в Recommendations",
                                ),
                            )
                        ),
                    ):
                        st.session_state["selected_variant_id"] = rec.variant.variant_id
                        st.session_state["guide_state"]["current_step_id"] = "step_plan"
                        st.success(
                            copy_text(
                                "pages.recommendations.selected_notice",
                                "Selected обновлён. Следующий шаг: Plan.",
                            )
                        )
                        st.session_state["page"] = "plan"
                        st.rerun()
                    if c2.button(
                        f"Open in Explore · {rec.variant.variant_id}",
                        key=f"rec-open-exp-{rec.variant.variant_id}",
                        help=action_contract_help(
                            build_action_contract(
                                label="Open in Explore",
                                intent=copy_text(
                                    "pages.recommendations.open_intent",
                                    "Посмотреть вариант на карте",
                                ),
                                effect=copy_text(
                                    "pages.recommendations.open_effect",
                                    "Откроет Explore с выбранной taxonomy/cell.",
                                ),
                                next_step=copy_text(
                                    "pages.recommendations.open_next",
                                    "Изучи связи и вернись к выбору",
                                ),
                                undo=copy_text(
                                    "pages.recommendations.open_undo",
                                    "Вернись на Recommendations через навигацию",
                                ),
                            )
                        ),
                    ):
                        st.session_state["selected_variant_id"] = rec.variant.variant_id
                        st.session_state["selected_cell_id"] = _variant_cell(rec.variant)
                        st.session_state["selected_taxonomy_id"] = _variant_taxonomy(rec.variant)
                        st.session_state["explore_tab"] = "Taxonomy"
                        st.session_state["page"] = "explore"
                        st.rerun()
                    c3.button(
                        f"Compare (SHOULD) · {rec.variant.variant_id}",
                        key=f"rec-compare-{rec.variant.variant_id}",
                    )

        _run_with_error_boundary(_render_recommendations)

    elif page_slug == "plan":
        _render_page_header("Plan")

        def _render_plan() -> None:
            report = _get_validation()
            _guard_fatals(report)
            variant_id = st.session_state.get("selected_variant_id")
            if not variant_id:
                _render_status(
                    "no_selection",
                    copy_text("pages.plan.not_ready", "Plan is not ready."),
                    reasons=[
                        copy_text(
                            "pages.plan.need_variant_reason",
                            "Select a variant in Recommendations.",
                        )
                    ],
                    level="warning",
                )
                return

            profile = st.session_state["profile"]
            classify_prefilter = st.session_state.get("classify_prefilter") or {}
            if classify_prefilter.get("from_classify"):
                st.info(
                    "Opened from Classify: "
                    f"taxonomy={classify_prefilter.get('taxonomy_id')} | "
                    f"cell={classify_prefilter.get('cell')}"
                )

            with st.spinner("Building plan..."):
                try:
                    plan = _ensure_plan(profile, variant_id)
                except ValueError as exc:
                    _render_status(
                        "error", "Plan generation failed.", reasons=[str(exc)], level="error"
                    )
                    return

            app_data = _get_app_data()
            variant = next(
                (item for item in app_data.variants if item.variant_id == variant_id), None
            )
            variant_stale = (
                is_variant_stale(variant, app_data.meta.staleness_policy)
                if variant is not None
                else False
            )

            st.session_state["plan"] = plan
            st.markdown(f"### Variant: {variant_id}")
            route = []
            if plan.week_plan:
                for week in sorted(plan.week_plan.keys()):
                    for title in plan.week_plan[week]:
                        if "Route:" in title:
                            route.append(title)
            st.caption("Route breadcrumb: " + (" / ".join(route[:2]) if route else "n/a"))
            if plan.legal_gate != "ok" or variant_stale:
                warns = []
                if plan.legal_gate != "ok":
                    warns.append(f"Legal gate: {plan.legal_gate}")
                if variant_stale:
                    warns.append("Variant data is stale")
                st.warning(" | ".join(warns))

            tab_checklist, tab_weeks, tab_compliance = st.tabs(
                ["Checklist", "4 weeks", "Compliance"]
            )

            with tab_checklist:
                st.markdown("#### Checklist")
                for idx, step in enumerate(plan.steps):
                    col_a, col_b = st.columns([0.8, 0.2])
                    with col_a:
                        done_key = f"plan-step-done-{step.id}"
                        st.checkbox(f"{step.title}", key=done_key)
                    with col_b:
                        if st.button("Details", key=f"plan-step-open-{step.id}"):
                            st.session_state["selected_plan_step_id"] = step.id
                            st.session_state["selected_plan_step_title"] = step.title
                            st.session_state["selected_plan_step_detail"] = step.detail

            with tab_weeks:
                st.markdown("#### 4-week outline")
                week_rows = []
                for week_name, items in plan.week_plan.items():
                    week_rows.append({"week": week_name, "items": " | ".join(items)})
                st.dataframe(week_rows, use_container_width=True)

            with tab_compliance:
                st.markdown("#### Compliance")
                st.write("Legal gate:", plan.legal_gate)
                for item in plan.compliance:
                    st.write(f"- {item}")

            with st.expander("Step detail drawer", expanded=False):
                step_id = st.session_state.get("selected_plan_step_id", "")
                if not step_id:
                    st.caption("Click Details on a checklist step to inspect step context.")
                else:
                    st.write(f"Step id: `{step_id}`")
                    st.write(f"Title: {st.session_state.get('selected_plan_step_title', '')}")
                    st.write(f"Detail: {st.session_state.get('selected_plan_step_detail', '')}")
                    st.caption("Outputs/artifacts: follow plan.md required artifacts section.")

            st.markdown("### Export preview")
            plan_text = render_plan_md(plan)
            st.download_button(
                "Preview plan.md",
                data=plan_text,
                file_name="plan.md",
                mime="text/markdown",
            )
            if st.button("Go to Export", key="plan-go-export"):
                st.session_state["page"] = "export"
                st.rerun()

        _run_with_error_boundary(_render_plan)

    elif page_slug == "export":
        _render_page_header("Export")

        def _render_export() -> None:
            report = _get_validation()
            _guard_fatals(report)
            variant_id = st.session_state.get("selected_variant_id")
            plan = st.session_state.get("plan")
            profile = st.session_state.get("profile")

            if not variant_id or plan is None:
                reasons = []
                if not variant_id:
                    reasons.append(
                        copy_text(
                            "pages.export.need_variant_reason",
                            "Select a variant in Recommendations.",
                        )
                    )
                if plan is None:
                    reasons.append(
                        copy_text(
                            "pages.export.need_plan_reason",
                            "Generate a plan in the Plan screen.",
                        )
                    )
                _render_status(
                    "not_ready",
                    copy_text("pages.export.not_ready", "Export is not ready."),
                    reasons=reasons,
                    level="warning",
                )
                return

            app_data = _get_app_data()
            recommendations = recommend(
                profile,
                app_data.variants,
                app_data.rulepack,
                app_data.meta.staleness_policy,
                profile.get("objective", "fastest_money"),
                {},
                len(app_data.variants),
            )
            selected_rec = next(
                (r for r in recommendations.ranked_variants if r.variant.variant_id == variant_id),
                None,
            )

            plan_text = render_plan_md(plan)
            result_payload = (
                render_result_json(
                    profile,
                    selected_rec,
                    plan,
                    diagnostics=recommendations.diagnostics,
                    profile_hash=recommendations.profile_hash,
                    meta=app_data.meta,
                    rulepack=app_data.rulepack,
                )
                if selected_rec
                else None
            )
            profile_yaml = yaml.safe_dump(profile, sort_keys=False, allow_unicode=True)

            st.markdown("### Artifacts")
            card1, card2, card3 = st.columns(3)
            with card1:
                st.markdown("**plan.md**")
                with st.expander("Preview plan.md"):
                    st.code(plan_text[:6000], language="markdown")
            with card2:
                st.markdown("**result.json**")
                with st.expander("Preview result.json"):
                    st.json(result_payload or {})
            with card3:
                st.markdown("**profile.yaml**")
                with st.expander("Preview profile.yaml"):
                    st.code(profile_yaml, language="yaml")

            st.markdown("### Export metadata")
            metadata_rows = [
                {"key": "dataset_version", "value": app_data.meta.dataset_version},
                {"key": "rulepack_reviewed_at", "value": app_data.rulepack.reviewed_at},
                {"key": "objective_preset", "value": profile.get("objective", "fastest_money")},
                {"key": "profile_hash", "value": st.session_state.get("profile_hash", "")},
            ]
            st.table(metadata_rows)

            run_cmd = (
                "money-map run --profile profiles/demo.yaml "
                f"--variant-id {variant_id} --out-dir exports"
            )
            st.code(run_cmd, language="bash")
            if st.button("Copy run command", key="export-copy-run-cmd"):
                st.info("Command shown above. Copy from code block.")

            if st.button("Generate export files", key="export-generate"):
                try:
                    paths = export_bundle(
                        profile_path=None,
                        variant_id=variant_id,
                        out_dir="exports",
                        data_dir="data",
                        profile_data=profile,
                    )
                except MoneyMapError as exc:
                    _render_error(exc)
                else:
                    st.session_state["export_paths"] = paths
                    st.success("Export completed")
                    st.write(paths)

            st.subheader("Downloads")
            st.download_button(
                "Download plan.md",
                data=plan_text,
                file_name="plan.md",
                mime="text/markdown",
            )
            st.download_button(
                "Download result.json",
                data=json.dumps(result_payload or {}, ensure_ascii=False, indent=2),
                file_name="result.json",
                mime="application/json",
                disabled=result_payload is None,
            )
            st.download_button(
                "Download profile.yaml",
                data=profile_yaml,
                file_name="profile.yaml",
                mime="text/yaml",
            )

        _run_with_error_boundary(_render_export)


if __name__ == "__main__":
    run_app()

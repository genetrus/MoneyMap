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
from money_map.ui.data_status import data_status_visibility
from money_map.ui.navigation import (
    NAV_ITEMS,
    NAV_LABEL_BY_SLUG,
    resolve_page_from_query,
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


def _init_state() -> None:
    st.session_state.setdefault("profile", DEFAULT_PROFILE.copy())
    st.session_state.setdefault(
        "filters",
        {"exclude_blocked": True, "exclude_not_feasible": False, "max_time_to_money_days": 60},
    )
    st.session_state.setdefault("selected_variant_id", "")
    st.session_state.setdefault("plan", None)
    st.session_state.setdefault("last_recommendations", None)
    st.session_state.setdefault("export_paths", None)
    st.session_state.setdefault("profile_source", "Demo profile")
    st.session_state.setdefault("ui_run_id", str(uuid4()))
    st.session_state.setdefault("page", "data-status")
    st.session_state.setdefault("theme_preset", "Light")
    st.session_state.setdefault("view_mode", "User")
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
        st.session_state["selected_variant_id"] = ""
        st.session_state["plan"] = None
        st.session_state["last_recommendations"] = None


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

        def _render_status() -> None:
            report = _get_validation()
            app_data = _get_app_data()
            warns_count = len(report["warns"])
            fatals_count = len(report["fatals"])
            warn_summary = _issue_summary(report["warns"])
            view_mode = get_view_mode()
            visibility = data_status_visibility(view_mode)

            status_label = report["status"].upper()
            status_class = {
                "valid": "valid",
                "invalid": "invalid",
                "stale": "stale",
            }.get(report["status"], "valid")

            col1, col2, col3 = st.columns(3)
            with col1:
                _render_kpi_card("Dataset version", str(report["dataset_version"]))
            with col2:
                _render_kpi_card("Reviewed at", str(report["reviewed_at"]))
            with col3:
                _render_kpi_card(
                    "Status", status_label, badge=status_label, badge_class=status_class
                )

            col4, col5, col6 = st.columns(3)
            with col4:
                _render_kpi_card("Warnings", str(warns_count), subtext=warn_summary or "")
            with col5:
                _render_kpi_card("Fatals", str(fatals_count))
            with col6:
                _render_kpi_card(
                    "Stale",
                    str(report["stale"]),
                    chip=f"Staleness policy: {report['staleness_policy_days']} days",
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
                if fatals_count > 0:
                    st.markdown("**FATAL issues (must fix)**")
                    st.table(_issue_rows(report["fatals"]))
                if warns_count > 0:
                    st.markdown("**Warnings (non-blocking)**")
                    st.table(_issue_rows(report["warns"]))

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
            classify_prefilter = st.session_state.get("classify_prefilter") or {}
            if classify_prefilter.get("from_classify"):
                st.info(
                    "Opened from Classify: "
                    f"taxonomy={classify_prefilter.get('taxonomy_id')} | "
                    f"cell={classify_prefilter.get('cell')}"
                )

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

            profile["name"] = st.text_input("Name", key="profile_name")
            profile["country"] = st.selectbox(
                "Country",
                ["DE"],
                index=0,
                key="profile_country",
            )
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
            profile["language_level"] = st.selectbox(
                "Language level",
                ["A1", "A2", "B1", "B2", "C1", "C2", "native"],
                index=["A1", "A2", "B1", "B2", "C1", "C2", "native"].index(
                    st.session_state.get("profile_language_level", "B1")
                ),
                key="profile_language_level",
            )
            profile["capital_eur"] = st.number_input(
                "Capital (EUR)",
                min_value=0,
                value=st.session_state.get("profile_capital_eur", profile["capital_eur"]),
                key="profile_capital_eur",
            )
            profile["time_per_week"] = st.number_input(
                "Time per week",
                min_value=0,
                value=st.session_state.get("profile_time_per_week", profile["time_per_week"]),
                key="profile_time_per_week",
            )
            assets_text = st.text_input("Assets (comma separated)", key="profile_assets_text")
            skills_text = st.text_input("Skills (comma separated)", key="profile_skills_text")
            constraints_text = st.text_area(
                "Constraints (comma separated)", key="profile_constraints_text"
            )

            profile["assets"] = [item.strip() for item in assets_text.split(",") if item.strip()]
            profile["skills"] = [item.strip() for item in skills_text.split(",") if item.strip()]
            profile["constraints"] = [
                item.strip() for item in constraints_text.split(",") if item.strip()
            ]

            st.session_state["profile"] = profile
            _sync_profile_session_state(profile)
            profile_validation = validate_profile(profile)
            if profile_validation["missing"]:
                st.info("Missing required fields: " + ", ".join(profile_validation["missing"]))
            for warning in profile_validation["warnings"]:
                st.warning(warning)
            st.caption(f"Profile hash: {st.session_state.get('profile_hash', '')}")
            if profile_validation["is_ready"]:
                st.success("Profile ready")
            else:
                st.caption("Profile draft")

        _run_with_error_boundary(_render_profile)

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

            tab_options = ["Matrix", "Taxonomy", "Bridges"]
            if st.session_state.get("explore_paths_enabled"):
                tab_options.append("Paths")
            if st.session_state.get("explore_library_enabled"):
                tab_options.append("Variants Library")
            selected_tab = st.radio("Explore tabs", tab_options, key="explore_tab", horizontal=True)

            with st.spinner("Building explore view..."):
                app_data = _get_app_data()
                variants = sorted(app_data.variants, key=_stable_variant_sort_key)

            _render_status("ready", f"Explore tab ready: {selected_tab}.")

            if selected_tab == "Matrix":
                selected_cell = st.selectbox("Cell", CELL_OPTIONS, key="explore_selected_cell")
                cell_variants = [v for v in variants if _variant_cell(v) == selected_cell]
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
                for variant in cell_variants:
                    _render_explore_variant_card(
                        variant,
                        taxonomy=_variant_taxonomy(variant),
                        cell=selected_cell,
                        stale=is_variant_stale(variant, app_data.meta.staleness_policy),
                    )

            elif selected_tab == "Taxonomy":
                selected_taxonomy = st.selectbox(
                    "Taxonomy",
                    TAXONOMY_OPTIONS,
                    key="explore_selected_taxonomy",
                )
                tax_variants = [v for v in variants if _variant_taxonomy(v) == selected_taxonomy]
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
                for variant in tax_variants:
                    _render_explore_variant_card(
                        variant,
                        taxonomy=selected_taxonomy,
                        cell=_variant_cell(variant),
                        stale=is_variant_stale(variant, app_data.meta.staleness_policy),
                    )

            elif selected_tab == "Bridges":
                selected_bridge = st.selectbox(
                    "Bridge",
                    BRIDGE_OPTIONS,
                    key="explore_selected_bridge",
                )
                frm, to = selected_bridge.split("->", 1)
                st.subheader(f"Bridge {frm} → {to}")
                bridge_variants = [v for v in variants if _variant_cell(v) in {frm, to}]
                st.write("Preconditions:")
                st.write("- Validate feasibility blockers")
                st.write("- Check legal gate for regulated domains")
                st.write("Steps:")
                st.write("- Prepare minimal artifacts")
                st.write("- Run recommendations with updated objective")
                if not bridge_variants:
                    _render_status(
                        "empty_view",
                        "No variants mapped to this bridge yet.",
                        reasons=["Use neighboring bridge or relax filters in Recommendations."],
                        level="warning",
                    )
                    return
                st.write("Common variants for this bridge:")
                for variant in bridge_variants:
                    _render_explore_variant_card(
                        variant,
                        taxonomy=_variant_taxonomy(variant),
                        cell=_variant_cell(variant),
                        stale=is_variant_stale(variant, app_data.meta.staleness_policy),
                    )

            elif selected_tab == "Paths":
                st.info("Paths hook is enabled but route templates are not implemented yet.")

            elif selected_tab == "Variants Library":
                st.info("Variants Library hook is enabled; advanced filters are pending.")

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
                    "Profile is not ready for recommendations.",
                    reasons=reasons,
                    level="warning",
                )
                return
            objective_options = ["fastest_money", "max_net"]
            current_objective = _ensure_objective(profile, objective_options)
            selected_objective = st.selectbox(
                "Objective preset",
                objective_options,
                index=objective_options.index(
                    st.session_state.get("rec_objective", current_objective)
                ),
                key="rec_objective",
            )
            st.caption("Objective preset affects ranking and diagnostics.")
            profile["objective"] = selected_objective
            st.session_state["profile"] = profile
            _sync_profile_session_state(profile)
            top_n = st.slider(
                "Top N",
                min_value=1,
                max_value=10,
                value=st.session_state.get("rec_top_n", 10),
                key="rec_top_n",
            )
            max_time = st.number_input(
                "Max time to first money (days)",
                value=int(st.session_state["filters"].get("max_time_to_money_days", 60)),
                key="rec_max_time_to_money_days",
            )
            st.session_state["filters"]["max_time_to_money_days"] = int(max_time)
            st.session_state["filters"]["exclude_blocked"] = st.checkbox(
                "Exclude blocked",
                value=st.session_state["filters"].get("exclude_blocked", True),
                key="rec_exclude_blocked",
            )
            st.session_state["filters"]["exclude_not_feasible"] = st.checkbox(
                "Exclude not feasible",
                value=st.session_state["filters"].get("exclude_not_feasible", False),
                key="rec_exclude_not_feasible",
            )

            def _run_recommendations() -> None:
                result = _get_recommendations(
                    json.dumps(profile, ensure_ascii=False),
                    st.session_state.get("objective_preset", profile["objective"]),
                    st.session_state["filters"],
                    top_n,
                )
                st.session_state["last_recommendations"] = result
                ranked_ids = {item.variant.variant_id for item in result.ranked_variants}
                selected = st.session_state.get("selected_variant_id")
                if selected and selected not in ranked_ids:
                    st.session_state["selected_variant_id"] = ""
                    st.session_state["plan"] = None

            if st.button("Run recommendations"):
                _run_recommendations()

            result = st.session_state.get("last_recommendations")
            if result is None:
                _render_status(
                    "not_ready",
                    "Run recommendations to see results.",
                    reasons=["No recommendations have been generated yet."],
                )
            elif not result.ranked_variants:
                _render_status(
                    "not_ready",
                    "No results found.",
                    reasons=["All candidates were filtered out by current constraints."],
                    level="warning",
                )
                if result.diagnostics.get("reasons"):
                    st.caption("Filtered out reasons:")
                    for reason, count in result.diagnostics["reasons"].items():
                        st.write(f"- {reason}: {count}")
                st.info("Quick fixes: relax filters or adjust objective.")
                if st.button("Allow not feasible"):
                    st.session_state["filters"]["exclude_not_feasible"] = False
                    _run_recommendations()
                if st.button("Allow blocked"):
                    st.session_state["filters"]["exclude_blocked"] = False
                    _run_recommendations()
                if st.button("Extend time window"):
                    st.session_state["filters"]["max_time_to_money_days"] = 60
                    _run_recommendations()
                return
            else:
                all_not_feasible = all(
                    rec.feasibility.status == "not_feasible" for rec in result.ranked_variants
                )
                if all_not_feasible:
                    st.warning("All results are currently not feasible.")
                    st.info("Quick fixes: loosen constraints or allow prep time.")
                    if st.button("Allow not feasible (show all)"):
                        st.session_state["filters"]["exclude_not_feasible"] = False
                        _run_recommendations()
                    if st.button("Extend time window"):
                        st.session_state["filters"]["max_time_to_money_days"] = 60
                        _run_recommendations()
                st.subheader("Reality Check")
                blocker_counts = Counter()
                for rec in result.ranked_variants:
                    blocker_counts.update(rec.feasibility.blockers)
                top_blockers = blocker_counts.most_common(3)
                if top_blockers:
                    formatted = ", ".join([f"{name} ({count})" for name, count in top_blockers])
                    st.warning("Top blockers: " + formatted)

                if result.diagnostics.get("reasons"):
                    st.caption("Diagnostics (filtered out):")
                    for reason, count in result.diagnostics["reasons"].items():
                        st.write(f"- {reason}: {count}")

                for rec in result.ranked_variants:
                    with st.container():
                        stale_label = " (stale)" if rec.stale else ""
                        st.subheader(rec.variant.title)
                        st.caption(f"ID: {rec.variant.variant_id}{stale_label}")
                        if rec.stale or rec.legal.legal_gate != "ok":
                            warnings = []
                            if rec.stale:
                                warnings.append("Variant data is stale")
                            if rec.legal.legal_gate != "ok":
                                warnings.append(f"Legal gate: {rec.legal.legal_gate}")
                            st.warning(" | ".join(warnings))

                        st.markdown("**Feasibility**")
                        st.write(f"Status: {rec.feasibility.status}")
                        if rec.feasibility.blockers:
                            st.write("Blockers: " + "; ".join(rec.feasibility.blockers))
                        if rec.feasibility.prep_steps:
                            st.write("Prep steps: " + "; ".join(rec.feasibility.prep_steps))
                        st.write(
                            "Prep estimate (weeks): "
                            + "–".join(map(str, rec.feasibility.estimated_prep_weeks_range))
                        )

                        st.markdown("**Economics**")
                        st.write(
                            "Time to first money (days): "
                            + "–".join(map(str, rec.economics.time_to_first_money_days_range))
                        )
                        st.write(
                            "Typical net/month: €"
                            + "–".join(map(str, rec.economics.typical_net_month_eur_range))
                        )
                        st.write(
                            "Costs range: €" + "–".join(map(str, rec.economics.costs_eur_range))
                        )
                        st.write(
                            f"Volatility/seasonality: {rec.economics.volatility_or_seasonality}"
                        )
                        st.write(f"Confidence: {rec.economics.confidence}")

                        st.markdown("**Legal Gate + Compliance**")
                        st.write(f"Gate: {rec.legal.legal_gate}")
                        if rec.legal.checklist:
                            st.write("Checklist: " + "; ".join(rec.legal.checklist))
                        if rec.legal.compliance_kits:
                            st.write("Kits: " + ", ".join(rec.legal.compliance_kits))

                        st.markdown("**Why this is in Top-N**")
                        st.write("; ".join(rec.pros))
                        if rec.cons:
                            st.markdown("**What can block you**")
                            st.write("; ".join(rec.cons))

                        if st.button(
                            f"Select {rec.variant.variant_id}",
                            key=f"select-{rec.variant.variant_id}",
                        ):
                            st.session_state["selected_variant_id"] = rec.variant.variant_id
                if st.button("Startable in 2 weeks"):
                    st.session_state["filters"]["max_time_to_money_days"] = 14
                    st.session_state["filters"]["exclude_blocked"] = True
                    _run_recommendations()
                if st.button("Focus on fastest money"):
                    profile["objective"] = "fastest_money"
                    st.session_state["filters"]["max_time_to_money_days"] = 30
                    st.session_state["profile"] = profile
                    _sync_profile_session_state(profile)
                    _run_recommendations()
                if st.button("Reduce legal friction"):
                    st.session_state["filters"]["exclude_blocked"] = True
                    _run_recommendations()

        _run_with_error_boundary(_render_recommendations)

    elif page_slug == "plan":
        _render_page_header("Plan")

        def _render_plan() -> None:
            report = _get_validation()
            _guard_fatals(report)
            variant_id = st.session_state.get("selected_variant_id")
            if not variant_id:
                _render_status(
                    "not_ready",
                    "Plan is not ready.",
                    reasons=["Select a variant in Recommendations."],
                )
            else:
                profile = st.session_state["profile"]
            classify_prefilter = st.session_state.get("classify_prefilter") or {}
            if classify_prefilter.get("from_classify"):
                st.info(
                    "Opened from Classify: "
                    f"taxonomy={classify_prefilter.get('taxonomy_id')} | "
                    f"cell={classify_prefilter.get('cell')}"
                )

                st.caption(f"Objective preset: {profile.get('objective', 'fastest_money')}")
                try:
                    plan = _ensure_plan(profile, variant_id)
                except ValueError as exc:
                    _render_status(
                        "error", "Plan generation failed.", reasons=[str(exc)], level="error"
                    )
                else:
                    app_data = _get_app_data()
                    variant = next(
                        (item for item in app_data.variants if item.variant_id == variant_id),
                        None,
                    )
                    variant_stale = (
                        is_variant_stale(variant, app_data.meta.staleness_policy)
                        if variant is not None
                        else False
                    )
                    if plan.legal_gate != "ok" or variant_stale:
                        warnings = []
                        if plan.legal_gate != "ok":
                            warnings.append(f"Legal gate: {plan.legal_gate}")
                        if variant_stale:
                            warnings.append("Variant data is stale")
                        st.warning(" | ".join(warnings))
                    st.session_state["plan"] = plan
                    st.write(f"Plan for {variant_id}")
                    st.write("Steps")
                    for step in plan.steps:
                        st.write(f"- {step.title}: {step.detail}")
                    st.write("4-week outline")
                    st.json(plan.week_plan)
                    st.write("Compliance")
                    st.write("\n".join(plan.compliance))

        _run_with_error_boundary(_render_plan)

    elif page_slug == "export":
        _render_page_header("Export")

        def _render_export() -> None:
            report = _get_validation()
            _guard_fatals(report)
            variant_id = st.session_state.get("selected_variant_id")
            plan = st.session_state.get("plan")
            if not variant_id or plan is None:
                reasons = []
                if not variant_id:
                    reasons.append("Select a variant in Recommendations.")
                if plan is None:
                    reasons.append("Generate a plan in the Plan screen.")
                _render_status("not_ready", "Export is not ready.", reasons=reasons)
            else:
                profile = st.session_state["profile"]
            classify_prefilter = st.session_state.get("classify_prefilter") or {}
            if classify_prefilter.get("from_classify"):
                st.info(
                    "Opened from Classify: "
                    f"taxonomy={classify_prefilter.get('taxonomy_id')} | "
                    f"cell={classify_prefilter.get('cell')}"
                )

                app_data = _get_app_data()
                plan_text = render_plan_md(plan)
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
                    (
                        r
                        for r in recommendations.ranked_variants
                        if r.variant.variant_id == variant_id
                    ),
                    None,
                )
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
                if selected_rec is None:
                    _render_status(
                        "error",
                        "Variant not found in recommendations.",
                        reasons=[f"Variant '{variant_id}' was not returned."],
                        level="error",
                    )

                if st.button("Generate export files"):
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
                    disabled=plan is None,
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
                    disabled=profile is None,
                )

        _run_with_error_boundary(_render_export)


if __name__ == "__main__":
    run_app()

"""Streamlit UI for MoneyMap walking skeleton."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import streamlit as st
import yaml

from money_map.app.api import export_bundle
from money_map.core.errors import InternalError, MoneyMapError
from money_map.core.graph import build_plan
from money_map.core.load import load_app_data
from money_map.core.recommend import is_variant_stale, recommend
from money_map.core.validate import validate
from money_map.render.plan_md import render_plan_md
from money_map.render.result_json import render_result_json
from money_map.storage.fs import read_yaml

DEFAULT_PROFILE = {
    "name": "Demo",
    "objective": "fastest_money",
    "language_level": "B1",
    "capital_eur": 300,
    "time_per_week": 15,
    "assets": ["laptop", "phone"],
    "location": "Berlin",
}


def _init_state() -> None:
    st.session_state.setdefault("profile", DEFAULT_PROFILE.copy())
    st.session_state.setdefault("filters", {"exclude_blocked": True})
    st.session_state.setdefault("selected_variant_id", "")
    st.session_state.setdefault("plan", None)
    st.session_state.setdefault("last_recommendations", None)
    st.session_state.setdefault("export_paths", None)
    st.session_state.setdefault("profile_source", "Demo profile")
    st.session_state.setdefault("ui_run_id", str(uuid4()))
    st.session_state.setdefault("data_status_preset", "Light")
    st.session_state.setdefault("page", "Data status")


def _render_error(err: MoneyMapError) -> None:
    run_id = err.run_id or st.session_state.get("ui_run_id", "unknown")
    st.error(f"[ERROR {err.code}] {err.message} (run_id={run_id})")
    if err.hint:
        st.info(f"Hint: {err.hint}")
    if err.details:
        st.caption(f"Details: {err.details}")


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
        st.error("Validation fatals block actions: " + ", ".join(_issue_codes(report["fatals"])))
        st.stop()


def _render_data_status_theme(preset: str, active_page: str) -> None:
    def _svg_data_uri(svg: str) -> str:
        return f"data:image/svg+xml;utf8,{quote(svg)}"

    icons = {
        "data_status": _svg_data_uri(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="black" d="M12 2C7.6 2 4 3.6 4 5.6v12.8C4 20.4 7.6 22 12 '
            "22s8-1.6 8-3.6V5.6C20 3.6 16.4 2 12 2zm0 2c3.6 0 6 .9 6 1.6S15.6 7.2 "
            "12 7.2s-6-.9-6-1.6S8.4 4 12 4zm0 6.2c3.6 0 6-.9 6-1.6V12c0 .7-2.4 "
            "1.6-6 1.6s-6-.9-6-1.6V8.6c0 .7 2.4 1.6 6 1.6zm0 6.2c3.6 0 6-.9 "
            '6-1.6v3.4c0 .7-2.4 1.6-6 1.6s-6-.9-6-1.6v-3.4c0 .7 2.4 1.6 6 1.6z"/>'
            "</svg>"
        ),
        "profile": _svg_data_uri(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="black" d="M12 12a4.2 4.2 0 1 0-4.2-4.2A4.2 4.2 0 0 0 12 '
            '12zm0 2c-3.5 0-6.8 1.8-6.8 4.2V20h13.6v-1.8C18.8 15.8 15.5 14 12 14z"/>'
            "</svg>"
        ),
        "recommendations": _svg_data_uri(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="black" d="M12 3.2l2.2 4.6 5.1.7-3.7 3.6.9 5.1L12 '
            '14.9 7.5 17.2l.9-5.1-3.7-3.6 5.1-.7L12 3.2z"/>'
            "</svg>"
        ),
        "plan": _svg_data_uri(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="black" d="M7 3h9a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 '
            '0 0 1-2-2V5a2 2 0 0 1 2-2zm2 5h7v2H9V8zm0 4h7v2H9v-2zm0 4h5v2H9v-2z"/>'
            "</svg>"
        ),
        "export": _svg_data_uri(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path fill="black" d="M12 3a1 1 0 0 1 1 1v8.6l2.4-2.4 1.4 1.4L12 '
            '16.4 7.2 11.6l1.4-1.4L11 12.6V4a1 1 0 0 1 1-1zm-7 15h14v2H5v-2z"/>'
            "</svg>"
        ),
    }

    palette = {
        "Light": {
            "bg": "#f5f6f8",
            "sidebar_bg": "#eef0f3",
            "card_bg": "#ffffff",
            "card_border": "#e3e6eb",
            "text": "#1f2328",
            "muted": "#5f6b7a",
            "shadow": "0 10px 30px rgba(15, 23, 42, 0.08)",
            "badge_valid": "#d7f5de",
            "badge_stale": "#ffe7c2",
            "badge_invalid": "#ffd7d9",
            "badge_text": "#1f2328",
            "chip_bg": "#e3f6e8",
            "chip_text": "#1b5e3c",
            "section_bg": "#ffffff",
            "divider": "#e5e7eb",
            "sidebar_divider": "#d4d9e1",
            "nav_hover_bg": "#e9edf3",
            "nav_active_bg": "#ffffff",
            "nav_active_border": "#d6dbe2",
            "nav_active_bar": "#3b82f6",
            "nav_icon": "#6b7280",
            "nav_icon_active": "#1f2328",
        },
        "Dark": {
            "bg": "#0f1724",
            "sidebar_bg": "#101827",
            "card_bg": "rgba(21, 30, 44, 0.7)",
            "card_border": "rgba(148, 163, 184, 0.2)",
            "text": "#e2e8f0",
            "muted": "#b6c1d1",
            "shadow": "0 16px 36px rgba(2, 6, 23, 0.35)",
            "badge_valid": "rgba(34, 197, 94, 0.25)",
            "badge_stale": "rgba(251, 191, 36, 0.25)",
            "badge_invalid": "rgba(239, 68, 68, 0.25)",
            "badge_text": "#f8fafc",
            "chip_bg": "rgba(34, 197, 94, 0.2)",
            "chip_text": "#c0f5d3",
            "section_bg": "rgba(17, 24, 39, 0.7)",
            "divider": "rgba(148, 163, 184, 0.2)",
            "sidebar_divider": "rgba(148, 163, 184, 0.25)",
            "nav_hover_bg": "rgba(30, 41, 59, 0.8)",
            "nav_active_bg": "rgba(30, 41, 59, 0.95)",
            "nav_active_border": "rgba(148, 163, 184, 0.3)",
            "nav_active_bar": "#38bdf8",
            "nav_icon": "#9aa6b8",
            "nav_icon_active": "#e2e8f0",
        },
    }
    theme = palette.get(preset, palette["Light"])
    st.markdown(
        f"""
        <style>
        :root {{
          --mm-bg: {theme["bg"]};
          --mm-sidebar-bg: {theme["sidebar_bg"]};
          --mm-card-bg: {theme["card_bg"]};
          --mm-card-border: {theme["card_border"]};
          --mm-text: {theme["text"]};
          --mm-muted: {theme["muted"]};
          --mm-shadow: {theme["shadow"]};
          --mm-badge-valid: {theme["badge_valid"]};
          --mm-badge-stale: {theme["badge_stale"]};
          --mm-badge-invalid: {theme["badge_invalid"]};
          --mm-badge-text: {theme["badge_text"]};
          --mm-chip-bg: {theme["chip_bg"]};
          --mm-chip-text: {theme["chip_text"]};
          --mm-section-bg: {theme["section_bg"]};
          --mm-divider: {theme["divider"]};
          --mm-sidebar-divider: {theme["sidebar_divider"]};
          --mm-nav-hover-bg: {theme["nav_hover_bg"]};
          --mm-nav-active-bg: {theme["nav_active_bg"]};
          --mm-nav-active-border: {theme["nav_active_border"]};
          --mm-nav-active-bar: {theme["nav_active_bar"]};
          --mm-nav-icon: {theme["nav_icon"]};
          --mm-nav-icon-active: {theme["nav_icon_active"]};
          --mm-icon-data-status: url("{icons["data_status"]}");
          --mm-icon-profile: url("{icons["profile"]}");
          --mm-icon-recommendations: url("{icons["recommendations"]}");
          --mm-icon-plan: url("{icons["plan"]}");
          --mm-icon-export: url("{icons["export"]}");
        }}

        .stApp {{
          background: var(--mm-bg);
          color: var(--mm-text);
        }}

        div[data-testid="stSidebar"] > div {{
          background: var(--mm-sidebar-bg);
        }}

        div[data-testid="stSidebar"] .mm-sidebar-header {{
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.75rem 0.5rem 0.4rem;
        }}

        div[data-testid="stSidebar"] .mm-sidebar-logo {{
          width: 28px;
          height: 28px;
          border-radius: 999px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(59, 130, 246, 0.18);
          box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.4);
        }}

        div[data-testid="stSidebar"] .mm-sidebar-title {{
          font-size: 1rem;
          font-weight: 600;
          color: var(--mm-text);
        }}

        div[data-testid="stSidebar"] .mm-sidebar-divider {{
          height: 1px;
          background: var(--mm-sidebar-divider);
          margin: 0.35rem 0.2rem 0.8rem;
        }}

        div[data-testid="stSidebar"] div[data-testid="stButton"] > button {{
          width: 100%;
          justify-content: flex-start;
          padding: 0.45rem 0.7rem 0.45rem 2.4rem;
          border-radius: 999px;
          border: 1px solid transparent;
          background: transparent;
          color: var(--mm-text);
          font-weight: 500;
          position: relative;
          box-shadow: none;
        }}

        div[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {{
          background: var(--mm-nav-hover-bg);
          border-color: transparent;
        }}

        div[data-testid="stSidebar"] div[data-testid="stButton"] > button::before {{
          content: "";
          position: absolute;
          left: 0.7rem;
          width: 18px;
          height: 18px;
          background-color: var(--mm-nav-icon);
          -webkit-mask-repeat: no-repeat;
          -webkit-mask-position: center;
          -webkit-mask-size: contain;
          mask-repeat: no-repeat;
          mask-position: center;
          mask-size: contain;
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="Data status"]::before {{
          -webkit-mask-image: var(--mm-icon-data-status);
          mask-image: var(--mm-icon-data-status);
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="Profile"]::before {{
          -webkit-mask-image: var(--mm-icon-profile);
          mask-image: var(--mm-icon-profile);
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="Recommendations"]::before {{
          -webkit-mask-image: var(--mm-icon-recommendations);
          mask-image: var(--mm-icon-recommendations);
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="Plan"]::before {{
          -webkit-mask-image: var(--mm-icon-plan);
          mask-image: var(--mm-icon-plan);
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="Export"]::before {{
          -webkit-mask-image: var(--mm-icon-export);
          mask-image: var(--mm-icon-export);
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="{active_page}"] {{
          background: var(--mm-nav-active-bg);
          border-color: var(--mm-nav-active-border);
          font-weight: 600;
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="{active_page}"]::before {{
          background-color: var(--mm-nav-icon-active);
        }}

        div[data-testid="stSidebar"]
          div[data-testid="stButton"]
          > button[aria-label="{active_page}"]::after {{
          content: "";
          position: absolute;
          left: 0.35rem;
          top: 50%;
          transform: translateY(-50%);
          width: 4px;
          height: 60%;
          border-radius: 999px;
          background: var(--mm-nav-active-bar);
        }}

        .main .block-container {{
          padding-top: 2.5rem;
          padding-bottom: 3rem;
        }}

        .data-status {{
          color: var(--mm-text);
        }}

        .data-status-header h1 {{
          font-size: 2rem;
          margin-bottom: 0.25rem;
        }}

        .data-status-header p {{
          font-size: 0.95rem;
          color: var(--mm-muted);
        }}

        .preset-selector label {{
          font-weight: 600;
          font-size: 0.8rem;
          color: var(--mm-muted);
        }}

        .preset-selector > div {{
          display: flex;
          justify-content: flex-end;
        }}

        .preset-selector div[role="radiogroup"] {{
          gap: 0.35rem;
        }}

        .preset-selector div[data-testid="stSelectbox"] {{
          max-width: 120px;
        }}

        .preset-selector div[data-testid="stSelectbox"] > div {{
          font-size: 0.8rem;
        }}

        .kpi-card {{
          background: var(--mm-card-bg);
          border-radius: 16px;
          border: 1px solid var(--mm-card-border);
          box-shadow: var(--mm-shadow);
          padding: 1rem 1.2rem;
          min-height: 110px;
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }}

        .kpi-label {{
          font-size: 0.75rem;
          letter-spacing: 0.02em;
          text-transform: uppercase;
          color: var(--mm-muted);
          font-weight: 600;
        }}

        .kpi-value {{
          font-size: 1.3rem;
          font-weight: 700;
          color: var(--mm-text);
        }}

        .kpi-subtext {{
          font-size: 0.8rem;
          color: var(--mm-muted);
        }}

        .kpi-badge {{
          display: inline-flex;
          align-items: center;
          padding: 0.2rem 0.6rem;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--mm-badge-text);
          text-transform: uppercase;
          letter-spacing: 0.03em;
        }}

        .kpi-badge.valid {{ background: var(--mm-badge-valid); }}
        .kpi-badge.stale {{ background: var(--mm-badge-stale); }}
        .kpi-badge.invalid {{ background: var(--mm-badge-invalid); }}

        .kpi-chip {{
          display: inline-flex;
          align-items: center;
          padding: 0.15rem 0.55rem;
          border-radius: 999px;
          background: var(--mm-chip-bg);
          color: var(--mm-chip-text);
          font-size: 0.72rem;
          font-weight: 600;
        }}

        .section-card {{
          background: var(--mm-section-bg);
          border: 1px solid var(--mm-card-border);
          border-radius: 18px;
          padding: 1.2rem 1.4rem;
          box-shadow: var(--mm-shadow);
          margin-top: 1.5rem;
        }}

        .section-card h3 {{
          margin-top: 0;
        }}

        .section-card p {{
          color: var(--mm-muted);
        }}

        .section-divider {{
          height: 1px;
          background: var(--mm-divider);
          margin: 1rem 0;
        }}

        .data-status table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 0.85rem;
        }}

        .data-status table th,
        .data-status table td {{
          border-bottom: 1px solid var(--mm-divider);
          padding: 0.5rem 0.6rem;
          text-align: left;
        }}

        .data-status table th {{
          color: var(--mm-muted);
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }}

        .data-status-disclaimer {{
          margin-top: 1.5rem;
          padding: 1rem 1.2rem;
          border-radius: 14px;
          background: var(--mm-card-bg);
          border: 1px solid var(--mm-card-border);
          color: var(--mm-muted);
        }}

        div[data-testid="stDownloadButton"] button {{
          border-radius: 999px;
          padding: 0.4rem 1rem;
          font-weight: 600;
        }}

        div[data-testid="stExpander"] {{
          border-radius: 14px;
          border: 1px solid var(--mm-card-border);
          background: var(--mm-section-bg);
        }}

        div[data-testid="stAlert"] {{
          border-radius: 14px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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

    st.sidebar.markdown(
        """
        <div class="mm-sidebar-header">
          <span class="mm-sidebar-logo">
            <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="9" fill="rgba(59,130,246,0.7)"></circle>
              <circle cx="12" cy="12" r="5" fill="rgba(14,116,144,0.6)"></circle>
            </svg>
          </span>
          <span class="mm-sidebar-title">MoneyMap</span>
        </div>
        <div class="mm-sidebar-divider"></div>
        """,
        unsafe_allow_html=True,
    )

    pages = ["Data status", "Profile", "Recommendations", "Plan", "Export"]
    for page_name in pages:
        if st.sidebar.button(page_name, key=f"nav-{page_name}", use_container_width=True):
            st.session_state["page"] = page_name

    page = st.session_state.get("page", "Data status")
    selected_preset = st.session_state.get("data_status_preset", "Light")
    _render_data_status_theme(selected_preset, page)

    if page == "Data status":
        preset_options = ["Light", "Dark"]

        st.markdown('<div class="data-status">', unsafe_allow_html=True)
        header_left, header_right = st.columns([0.75, 0.25])
        with header_left:
            st.markdown(
                """
                <div class="data-status-header">
                  <h1>Data status</h1>
                  <p>Validation, staleness, and dataset metadata (offline-first).</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with header_right:
            st.markdown('<div class="preset-selector">', unsafe_allow_html=True)
            st.selectbox(
                "",
                preset_options,
                index=preset_options.index(st.session_state.get("data_status_preset", "Light")),
                key="data_status_preset",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        def _render_status() -> None:
            report = _get_validation()
            app_data = _get_app_data()
            warns_count = len(report["warns"])
            fatals_count = len(report["fatals"])
            warn_summary = _issue_summary(report["warns"])

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
                    "Reviewed_at is older than staleness_policy. Show warnings and apply cautious "
                    "behavior.\n\n"
                    "For regulated domains: force legal_gate=require_check when rulepack is stale."
                )
            else:
                st.caption("Data is valid.")

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Validate report")
            report_json = json.dumps(report, ensure_ascii=False, indent=2, default=str)
            safe_ts = report["generated_at"].replace(":", "-")
            file_name = f"money_map_validate_report__{report['dataset_version']}__{safe_ts}.json"
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
            with st.expander("Raw report JSON"):
                st.json(report)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("Validation summary")
            if fatals_count > 0:
                st.markdown("**FATAL issues (must fix)**")
                st.table(_issue_rows(report["fatals"]))
            if warns_count > 0:
                st.markdown("**Warnings (non-blocking)**")
                st.table(_issue_rows(report["warns"]))

            with st.expander("Staleness details"):
                st.write("RulePack: DE")
                st.write(f"rulepack_reviewed_at: {app_data.rulepack.reviewed_at}")
                st.write(f"staleness_policy_days: {report['staleness_policy_days']}")
                rulepack_stale = report["staleness"]["rulepack"].get("is_stale")
                st.write(f"rulepack_stale: {rulepack_stale}")
                variant_dates = [
                    variant.review_date for variant in app_data.variants if variant.review_date
                ]
                st.write(f"variants_count: {len(app_data.variants)}")
                if variant_dates:
                    st.write(f"oldest_variant_review_date: {min(variant_dates)}")
                    st.write(f"newest_variant_review_date: {max(variant_dates)}")
                variants_stale = any(
                    detail.get("is_stale") for detail in report["staleness"]["variants"].values()
                )
                st.write(f"variants_stale: {variants_stale}")
                st.caption(
                    "If rulepack/variants are stale: show warning. For regulated domains apply "
                    "cautious behavior (force require_check)."
                )

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
                            "Schema version": str(rulepack_payload.get("schema_version", "")),
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
                            "Schema version": str(variants_payload.get("schema_version", "")),
                            "Items": len(variants_payload.get("variants", [])),
                        }
                    )
                if sources:
                    st.table(sources)

                st.write(
                    "Reproducibility gate: one script/process should rebuild the same dataset "
                    "from sources."
                )
                st.write(
                    "Errors must be diagnosable: this page shows validation report + sources; "
                    "use the report to locate failing items."
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

    elif page == "Profile":
        st.header("Profile")

        def _render_profile() -> None:
            repo_root = Path(__file__).resolve().parents[3]
            profiles_dir = repo_root / "profiles"
            demo_profiles = sorted([path.name for path in profiles_dir.glob("*.yaml")])
            if demo_profiles:
                selected = st.selectbox(
                    "Load demo profile",
                    ["Demo profile"] + demo_profiles,
                    index=0,
                )
                if selected != st.session_state.get("profile_source"):
                    st.session_state["profile_source"] = selected
                    if selected != "Demo profile":
                        try:
                            st.session_state["profile"] = read_yaml(profiles_dir / selected)
                        except ValueError as exc:
                            st.error(str(exc))
            st.caption(f"Profile source: {st.session_state['profile_source']}")
            quick_mode = st.toggle("Quick mode", value=True)
            profile = st.session_state["profile"]
            profile.setdefault("name", "")
            profile.setdefault("location", "")
            profile.setdefault("language_level", "B1")
            profile.setdefault("capital_eur", 0)
            profile.setdefault("time_per_week", 0)
            profile.setdefault("assets", [])

            profile["name"] = st.text_input("Name", value=profile["name"])
            profile["location"] = st.text_input("Location", value=profile["location"])
            profile["language_level"] = st.selectbox(
                "Language level",
                ["A1", "A2", "B1", "B2", "C1", "C2", "native"],
                index=2,
            )
            profile["capital_eur"] = st.number_input("Capital (EUR)", value=profile["capital_eur"])
            profile["time_per_week"] = st.number_input(
                "Time per week", value=profile["time_per_week"]
            )
            if not quick_mode:
                assets = st.text_input(
                    "Assets (comma separated)",
                    value=", ".join(profile["assets"]),
                )
                profile["assets"] = [item.strip() for item in assets.split(",") if item.strip()]

            st.session_state["profile"] = profile
            st.success("Profile ready" if profile["name"] else "Profile draft")

        _run_with_error_boundary(_render_profile)

    elif page == "Recommendations":
        st.header("Recommendations")

        def _render_recommendations() -> None:
            report = _get_validation()
            _guard_fatals(report)
            profile = st.session_state["profile"]
            objective_options = ["fastest_money", "max_net"]
            current_objective = _ensure_objective(profile, objective_options)
            selected_objective = st.selectbox(
                "Objective preset",
                objective_options,
                index=objective_options.index(current_objective),
            )
            st.caption("Objective preset affects ranking and diagnostics.")
            profile["objective"] = selected_objective
            st.session_state["profile"] = profile
            top_n = st.slider("Top N", min_value=1, max_value=10, value=10)
            max_time = st.number_input(
                "Max time to first money (days)",
                value=int(st.session_state["filters"].get("max_time_to_money_days", 60)),
            )
            st.session_state["filters"]["max_time_to_money_days"] = int(max_time)
            st.session_state["filters"]["exclude_blocked"] = st.checkbox(
                "Exclude blocked",
                value=st.session_state["filters"].get("exclude_blocked", True),
            )

            def _run_recommendations() -> None:
                result = _get_recommendations(
                    json.dumps(profile, ensure_ascii=False),
                    profile["objective"],
                    st.session_state["filters"],
                    top_n,
                )
                st.session_state["last_recommendations"] = result

            if st.button("Run recommendations"):
                _run_recommendations()

            result = st.session_state.get("last_recommendations")
            if result is None:
                st.info("Run recommendations to see results.")
            elif not result.ranked_variants:
                st.warning("No results. Adjust filters and try again.")
            else:
                for rec in result.ranked_variants:
                    st.subheader(rec.variant.title)
                    st.caption(rec.variant.variant_id)
                    stale_label = " (stale)" if rec.stale else ""
                    st.write(
                        f"Feasibility: {rec.feasibility.status} | "
                        f"Legal: {rec.legal.legal_gate}{stale_label}"
                    )
                    if rec.stale or rec.legal.legal_gate != "ok":
                        warnings = []
                        if rec.stale:
                            warnings.append("Variant data is stale")
                        if rec.legal.legal_gate != "ok":
                            warnings.append(f"Legal gate: {rec.legal.legal_gate}")
                        st.warning(" | ".join(warnings))
                    st.write("Why: " + "; ".join(rec.pros))
                    if rec.cons:
                        st.write("Concerns: " + "; ".join(rec.cons))
                    if st.button(
                        f"Select {rec.variant.variant_id}",
                        key=f"select-{rec.variant.variant_id}",
                    ):
                        st.session_state["selected_variant_id"] = rec.variant.variant_id

                st.subheader("Reality Check")
                blocker_counts = Counter()
                for rec in result.ranked_variants:
                    blocker_counts.update(rec.feasibility.blockers)
                top_blockers = blocker_counts.most_common(3)
                if top_blockers:
                    formatted = ", ".join([f"{name} ({count})" for name, count in top_blockers])
                    st.warning("Top blockers: " + formatted)
                if st.button("Startable in 2 weeks"):
                    st.session_state["filters"]["max_time_to_money_days"] = 14
                    st.session_state["filters"]["exclude_blocked"] = True
                    _run_recommendations()
                if st.button("Focus on fastest money"):
                    profile["objective"] = "fastest_money"
                    st.session_state["filters"]["max_time_to_money_days"] = 30
                    st.session_state["profile"] = profile
                    _run_recommendations()
                if st.button("Reduce legal friction"):
                    st.session_state["filters"]["exclude_blocked"] = True
                    _run_recommendations()

        _run_with_error_boundary(_render_recommendations)

    elif page == "Plan":
        st.header("Plan")

        def _render_plan() -> None:
            report = _get_validation()
            _guard_fatals(report)
            variant_id = st.session_state.get("selected_variant_id")
            if not variant_id:
                st.info("Select a variant in Recommendations.")
            else:
                profile = st.session_state["profile"]
                st.caption(f"Objective preset: {profile.get('objective', 'fastest_money')}")
                try:
                    plan = _ensure_plan(profile, variant_id)
                except ValueError as exc:
                    st.error(str(exc))
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

    elif page == "Export":
        st.header("Export")

        def _render_export() -> None:
            report = _get_validation()
            _guard_fatals(report)
            variant_id = st.session_state.get("selected_variant_id")
            plan = st.session_state.get("plan")
            if not variant_id or plan is None:
                st.info("Select a variant and generate a plan first.")
            else:
                profile = st.session_state["profile"]
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
                    )
                    if selected_rec
                    else None
                )
                profile_yaml = yaml.safe_dump(profile, sort_keys=False, allow_unicode=True)
                if selected_rec is None:
                    st.error(f"Variant '{variant_id}' not found in recommendations.")

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

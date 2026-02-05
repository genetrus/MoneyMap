"""Theme helpers for the MoneyMap Streamlit UI."""

from __future__ import annotations

import base64

THEME_PRESETS: dict[str, dict[str, str]] = {
    "Light": {
        "bg": "#f5f6f8",
        "sidebar_bg": "#eef0f3",
        "card_bg": "#ffffff",
        "card_border": "#e3e6eb",
        "text": "#1f2328",
        "muted": "#5f6b7a",
        "link": "#2563eb",
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
        "logo_bg": "rgba(59, 130, 246, 0.18)",
        "logo_border": "rgba(148, 163, 184, 0.4)",
        "control_bg": "#ffffff",
        "control_border": "#d4d9e1",
        "control_text": "#1f2328",
        "button_bg": "#2563eb",
        "button_text": "#ffffff",
        "button_border": "#1d4ed8",
    },
    "Dark": {
        "bg": "#0f1724",
        "sidebar_bg": "#101827",
        "card_bg": "rgba(21, 30, 44, 0.7)",
        "card_border": "rgba(148, 163, 184, 0.2)",
        "text": "#e2e8f0",
        "muted": "#b6c1d1",
        "link": "#7dd3fc",
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
        "logo_bg": "rgba(56, 189, 248, 0.16)",
        "logo_border": "rgba(148, 163, 184, 0.5)",
        "control_bg": "rgba(15, 23, 42, 0.6)",
        "control_border": "rgba(148, 163, 184, 0.3)",
        "control_text": "#e2e8f0",
        "button_bg": "#38bdf8",
        "button_text": "#0f1724",
        "button_border": "#0ea5e9",
    },
}


def _svg_data_uri_base64(svg: str) -> str:
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


ICONS = {
    "data_status": _svg_data_uri_base64(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="black" stroke-width="1.7" stroke-linecap="round" '
        'stroke-linejoin="round">'
        '<ellipse cx="12" cy="5" rx="7" ry="3"></ellipse>'
        '<path d="M5 5v9c0 1.7 3.1 3 7 3s7-1.3 7-3V5"></path>'
        '<path d="M5 10c0 1.7 3.1 3 7 3s7-1.3 7-3"></path>'
        "</svg>"
    ),
    "profile": _svg_data_uri_base64(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="black" stroke-width="1.7" stroke-linecap="round" '
        'stroke-linejoin="round">'
        '<circle cx="12" cy="8" r="3.2"></circle>'
        '<path d="M5 20c1.2-3.6 4.2-5.4 7-5.4s5.8 1.8 7 5.4"></path>'
        "</svg>"
    ),
    "recommendations": _svg_data_uri_base64(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="black" stroke-width="1.7" stroke-linecap="round" '
        'stroke-linejoin="round">'
        "<path "
        'd="M12 3l2.2 4.6 5.1.7-3.7 3.6.9 5.1L12 14.9 '
        '7.5 17.2l.9-5.1-3.7-3.6 5.1-.7L12 3z"></path>'
        "</svg>"
    ),
    "plan": _svg_data_uri_base64(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="black" stroke-width="1.7" stroke-linecap="round" '
        'stroke-linejoin="round">'
        "<path "
        'd="M7 3h9a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"></path>'
        '<path d="M9 8h7M9 12h7M9 16h5"></path>'
        "</svg>"
    ),
    "export": _svg_data_uri_base64(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="black" stroke-width="1.7" stroke-linecap="round" '
        'stroke-linejoin="round">'
        '<path d="M12 3v10"></path>'
        '<path d="M8 9l4 4 4-4"></path>'
        '<path d="M5 20h14"></path>'
        "</svg>"
    ),
}


def build_theme_css(theme_name: str) -> str:
    theme = THEME_PRESETS.get(theme_name, THEME_PRESETS["Light"])
    return f"""
    <style>
    :root {{
      color-scheme: {"dark" if theme_name == "Dark" else "light"};
      --mm-bg: {theme["bg"]};
      --mm-sidebar-bg: {theme["sidebar_bg"]};
      --mm-card-bg: {theme["card_bg"]};
      --mm-card-border: {theme["card_border"]};
      --mm-text: {theme["text"]};
      --mm-muted: {theme["muted"]};
      --mm-link: {theme["link"]};
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
      --mm-logo-bg: {theme["logo_bg"]};
      --mm-logo-border: {theme["logo_border"]};
      --mm-control-bg: {theme["control_bg"]};
      --mm-control-border: {theme["control_border"]};
      --mm-control-text: {theme["control_text"]};
      --mm-button-bg: {theme["button_bg"]};
      --mm-button-text: {theme["button_text"]};
      --mm-button-border: {theme["button_border"]};
      --mm-icon-data-status: url("{ICONS["data_status"]}");
      --mm-icon-profile: url("{ICONS["profile"]}");
      --mm-icon-recommendations: url("{ICONS["recommendations"]}");
      --mm-icon-plan: url("{ICONS["plan"]}");
      --mm-icon-export: url("{ICONS["export"]}");
    }}

    .stApp {{
      background: var(--mm-bg);
      color: var(--mm-text);
    }}

    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp h5,
    .stApp h6 {{
      color: var(--mm-text);
    }}

    .stApp a,
    .stApp a:visited {{
      color: var(--mm-link);
      text-decoration: none;
    }}

    .stApp a:hover {{
      text-decoration: underline;
    }}

    div[data-testid="stSidebar"] > div {{
      background: var(--mm-sidebar-bg);
    }}

    .mm-sidebar {{
      color: var(--mm-text);
    }}

    .mm-sidebar-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.6rem;
      padding: 0.75rem 0.5rem 0.4rem;
    }}

    .mm-sidebar-brand {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    .mm-sidebar-logo {{
      width: 28px;
      height: 28px;
      border-radius: 999px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--mm-logo-bg);
      box-shadow: inset 0 0 0 1px var(--mm-logo-border);
    }}

    .mm-sidebar-title {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--mm-text);
    }}

    .mm-theme-switch div[data-testid="stSelectbox"] {{
      max-width: 110px;
    }}

    .mm-theme-switch div[data-testid="stSelectbox"] > div {{
      font-size: 0.78rem;
      border-radius: 12px;
      border: 1px solid var(--mm-control-border);
      background: var(--mm-control-bg);
      color: var(--mm-control-text);
    }}

    .mm-theme-switch div[data-testid="stSelectbox"] div[role="combobox"] {{
      min-height: 30px;
      padding: 0.1rem 0.4rem;
    }}

    .mm-page-header {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.6rem;
    }}

    .mm-page-header h1 {{
      font-size: 1.85rem;
      margin-bottom: 0.25rem;
    }}

    .mm-page-header p {{
      font-size: 0.95rem;
      color: var(--mm-muted);
    }}

    .mm-sidebar-section-title {{
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--mm-muted);
      padding: 0.3rem 0.7rem 0.4rem;
    }}

    .mm-sidebar-divider {{
      height: 1px;
      background: var(--mm-sidebar-divider);
      margin: 0.35rem 0.2rem 0.6rem;
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] > div {{
      gap: 0.25rem;
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.45rem 0.7rem 0.45rem 2.2rem;
      border-radius: 999px;
      border: 1px solid transparent;
      color: inherit;
      font-weight: 500;
      text-decoration: none;
      position: relative;
      transition: background 120ms ease, border 120ms ease;
      width: 100%;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:hover {{
      background: var(--mm-nav-hover-bg);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label::before {{
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

    #mm-nav-anchor + div[data-testid="stRadio"] label:nth-of-type(1)::before {{
      -webkit-mask-image: var(--mm-icon-data-status);
      mask-image: var(--mm-icon-data-status);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:nth-of-type(2)::before {{
      -webkit-mask-image: var(--mm-icon-profile);
      mask-image: var(--mm-icon-profile);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:nth-of-type(3)::before {{
      -webkit-mask-image: var(--mm-icon-recommendations);
      mask-image: var(--mm-icon-recommendations);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:nth-of-type(4)::before {{
      -webkit-mask-image: var(--mm-icon-plan);
      mask-image: var(--mm-icon-plan);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:nth-of-type(5)::before {{
      -webkit-mask-image: var(--mm-icon-export);
      mask-image: var(--mm-icon-export);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input[value="data-status"])::before {{
      -webkit-mask-image: var(--mm-icon-data-status);
      mask-image: var(--mm-icon-data-status);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input[value="profile"])::before {{
      -webkit-mask-image: var(--mm-icon-profile);
      mask-image: var(--mm-icon-profile);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input[value="recommendations"])::before {{
      -webkit-mask-image: var(--mm-icon-recommendations);
      mask-image: var(--mm-icon-recommendations);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input[value="plan"])::before {{
      -webkit-mask-image: var(--mm-icon-plan);
      mask-image: var(--mm-icon-plan);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input[value="export"])::before {{
      -webkit-mask-image: var(--mm-icon-export);
      mask-image: var(--mm-icon-export);
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input:checked) {{
      background: var(--mm-nav-active-bg);
      border-radius: 999px;
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input:checked) {{
      font-weight: 600;
    }}

    #mm-nav-anchor + div[data-testid="stRadio"] label:has(input:checked)::before {{
      background-color: var(--mm-nav-icon-active);
    }}

    .data-status {{
      color: var(--mm-text);
      padding-top: 0.3rem;
    }}

    .data-status .kpi-card {{
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

    .data-status .kpi-label {{
      font-size: 0.75rem;
      letter-spacing: 0.02em;
      text-transform: uppercase;
      color: var(--mm-muted);
      font-weight: 600;
    }}

    .data-status .kpi-value {{
      font-size: 1.18rem;
      font-weight: 700;
      color: var(--mm-text);
    }}

    .data-status .kpi-subtext {{
      font-size: 0.8rem;
      color: var(--mm-muted);
    }}

    .data-status .kpi-badge {{
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

    .data-status .kpi-badge.valid {{ background: var(--mm-badge-valid); }}
    .data-status .kpi-badge.stale {{ background: var(--mm-badge-stale); }}
    .data-status .kpi-badge.invalid {{ background: var(--mm-badge-invalid); }}

    .data-status .kpi-chip {{
      display: inline-flex;
      align-items: center;
      padding: 0.15rem 0.55rem;
      border-radius: 999px;
      background: var(--mm-chip-bg);
      color: var(--mm-chip-text);
      font-size: 0.72rem;
      font-weight: 600;
    }}

    .data-status .section-card {{
      background: var(--mm-section-bg);
      border: 1px solid var(--mm-card-border);
      border-radius: 16px;
      padding: 1.2rem 1.4rem;
      box-shadow: var(--mm-shadow);
      margin-top: 1.5rem;
    }}

    .data-status .section-card h3 {{
      margin-top: 0;
    }}

    .data-status .section-card p {{
      color: var(--mm-muted);
    }}

    .data-status .section-divider {{
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

    div[data-testid="stDownloadButton"] button,
    div[data-testid="stButton"] button {{
      border-radius: 999px;
      padding: 0.4rem 1rem;
      font-weight: 600;
      background: var(--mm-button-bg);
      color: var(--mm-button-text);
      border: 1px solid var(--mm-button-border);
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
    """


def inject_global_theme(preset: str) -> None:
    import streamlit as st

    st.markdown(build_theme_css(preset), unsafe_allow_html=True)

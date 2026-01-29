from __future__ import annotations

import argparse
from pathlib import Path

import streamlit as st

from money_map.i18n import t
from money_map.ui.views import (
    data_editor,
    data_explorer,
    data_status,
    export,
    plan,
    profile,
    recommendations,
)

LANG_OPTIONS = ["en", "de", "fr", "es", "pl", "ru"]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--data-dir", default="data")
    return parser.parse_known_args()[0]


def main() -> None:
    args = _parse_args()
    data_dir = Path(args.data_dir)

    st.set_page_config(page_title=t("app.title", "en"), layout="wide")
    if "lang" not in st.session_state:
        st.session_state["lang"] = "en"

    lang = st.sidebar.selectbox(
        t("common.language", st.session_state["lang"]),
        options=LANG_OPTIONS,
        index=LANG_OPTIONS.index(st.session_state["lang"]),
    )
    st.session_state["lang"] = lang

    nav_labels = {
        "data_status": t("nav.data_status", lang),
        "data_explorer": t("nav.data_explorer", lang),
        "data_editor": t("nav.data_editor", lang),
        "profile": t("nav.profile", lang),
        "recommendations": t("nav.recommendations", lang),
        "plan": t("nav.plan", lang),
        "export": t("nav.export", lang),
    }

    selection = st.sidebar.radio(
        "", list(nav_labels.keys()), format_func=lambda key: nav_labels[key]
    )

    if selection == "data_status":
        data_status.render(data_dir, lang)
    elif selection == "data_explorer":
        data_explorer.render(data_dir, lang)
    elif selection == "data_editor":
        data_editor.render(data_dir, lang)
    elif selection == "profile":
        profile.render(data_dir, lang)
    elif selection == "recommendations":
        recommendations.render(data_dir, lang)
    elif selection == "plan":
        plan.render(data_dir, lang)
    elif selection == "export":
        export.render(data_dir, lang)


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

import streamlit as st

from money_map.core.load import load_app_data
from money_map.core.model import UserProfile
from money_map.core.plan import build_plan
from money_map.i18n import t
from money_map.i18n.locale import format_date, format_int


def render(data_dir: Path, lang: str, workspace: Path | None = None) -> None:
    st.header(t("ui.plan.header", lang))
    selected = st.session_state.get("selected_variant_id")
    if not selected:
        st.info(t("ui.plan.no_selection", lang))
        return

    profile: UserProfile = st.session_state.get("profile")
    if profile is None:
        st.info(t("ui.common.load_profile_first", lang))
        return

    appdata = load_app_data(data_dir, workspace=workspace)
    plan = build_plan(selected, profile, appdata)

    st.subheader(t("ui.plan.overview", lang))
    st.write(
        f"- {t('planner.overview.goal', lang)}: "
        f"{t(plan.overview.get('goal_variant_key', ''), lang)}"
    )
    st.write(
        f"- {t('planner.overview.time_budget', lang)}: "
        f"{format_int(plan.overview.get('time_hours_per_week', 0), lang)} "
        f"{t('planner.units.hours_per_week', lang)}"
    )
    if plan.overview.get("constraints"):
        st.write(
            f"- {t('planner.overview.constraints', lang)}: "
            f"{', '.join([t(item, lang) for item in plan.overview.get('constraints', [])])}"
        )

    st.subheader(t("ui.plan.week_plan", lang))
    for step in plan.steps:
        with st.expander(
            f"{t(step.get('title_key', ''), lang)} "
            f"({t('planner.week_label', lang, week=step.get('week'))})",
            expanded=False,
        ):
            st.write(
                f"{t('planner.estimated_hours', lang)}: "
                f"{format_int(step.get('estimated_hours', 0), lang)}"
            )
            st.write(f"**{t('planner.actions', lang)}**")
            for action in step.get("actions", []):
                st.write(f"- {t(action, lang)}")
            st.write(f"**{t('planner.outputs', lang)}**")
            for output in step.get("outputs", []):
                st.write(f"- {t(output, lang)}")
            if step.get("checks"):
                st.write(f"**{t('planner.checks', lang)}**")
                for check in step.get("checks", []):
                    st.write(f"- {t(check, lang)}")

    st.subheader(t("ui.plan.compliance_checklist", lang))
    if plan.compliance_checklist:
        for item in plan.compliance_checklist:
            st.write(f"- {t(item, lang)}")
    else:
        st.write(f"- {t('planner.compliance.none', lang)}")

    st.subheader(t("ui.plan.next_reviews", lang))
    for review in plan.next_reviews:
        st.write(
            f"- {t(review.get('item_key', ''), lang)}: "
            f"{format_date(review.get('due_date'), lang)}"
        )

    st.subheader(t("ui.plan.artifacts", lang))
    for artifact in plan.artifacts:
        st.write(
            f"- {artifact.get('filename')}: {t(artifact.get('description_key', ''), lang)}"
        )

from __future__ import annotations

from pathlib import Path

import streamlit as st

from datetime import date
from money_map.core.load import load_app_data
from money_map.core.model import UserProfile
from money_map.core.recommend import recommend
from money_map.core.reviews import load_reviews
from money_map.core.simulate import simulate_variant
from money_map.core.workspace import get_workspace_paths
from money_map.i18n import t
from money_map.i18n.locale import format_currency, format_percent


def render(data_dir: Path, lang: str, workspace: Path | None = None) -> None:
    st.header(t("ui.reco.header", lang))
    appdata = load_app_data(data_dir, workspace=workspace)

    profile: UserProfile = st.session_state.get("profile")
    if profile is None:
        st.info(t("ui.common.load_profile_first", lang))
        return

    presets = appdata.presets
    preset_ids = [preset.preset_id for preset in presets]
    preset_index = (
        preset_ids.index(profile.objective_preset)
        if profile.objective_preset in preset_ids
        else 0
    )
    objective = st.selectbox(
        t("ui.reco.objective_preset", lang),
        options=preset_ids,
        index=preset_index,
        format_func=lambda preset_id: t(
            next(
                (preset.title_key for preset in presets if preset.preset_id == preset_id),
                preset_id,
            ),
            lang,
        ),
    )

    if st.button(t("common.recommend", lang)):
        profile.objective_preset = objective
        reviews = None
        if workspace is not None:
            reviews = load_reviews(get_workspace_paths(workspace).reviews / "reviews.yaml")
        result = recommend(profile, appdata, top_n=5, reviews=reviews)
        st.session_state["recommendations"] = result

    result = st.session_state.get("recommendations")
    if result:
        variant_by_id = {variant.variant_id: variant for variant in appdata.variants}
        kit_by_id = {
            kit.kit_id: kit
            for kit in appdata.rulepack.compliance_kits
        }
        for item in result.ranked_variants:
            payload = item.model_dump() if hasattr(item, "model_dump") else item
            variant = variant_by_id[payload["variant_id"]]
            st.subheader(t(variant.title_key, lang))
            st.write(t(variant.summary_key, lang))
            st.caption(
                f"{t('ui.reco.score_total', lang)}: "
                f"{format_percent(payload['score_total'], lang)}"
            )
            st.write(f"**{t('ui.reco.score_breakdown', lang)}**")
            for key in ("feasibility", "economics", "legal", "fit", "staleness"):
                st.write(f"{t(f'ui.reco.score.{key}', lang)}")
                st.progress(min(1.0, payload["score_breakdown"].get(key, 0) / 100))

            st.write(f"**{t('ui.reco.pros', lang)}**")
            for reason in payload.get("pros", []):
                st.write(f"- {t(reason, lang)}")
            st.write(f"**{t('ui.reco.cons', lang)}**")
            for reason in payload.get("cons", []):
                st.write(f"- {t(reason, lang)}")
            st.write(f"**{t('ui.reco.blockers', lang)}**")
            if payload.get("blockers"):
                for reason in payload.get("blockers", []):
                    st.write(f"- {t(reason, lang)}")
            else:
                st.write(f"- {t('ui.reco.none', lang)}")
            st.write(f"**{t('ui.reco.assumptions', lang)}**")
            for reason in payload.get("assumptions", []):
                st.write(f"- {t(reason, lang)}")
            sim_result = simulate_variant(
                profile,
                variant,
                appdata.presets[0] if appdata.presets else None,
                6,
                date.today(),
            )
            if sim_result.months:
                st.caption(
                    t(
                        "ui.simulation.six_month_net",
                        lang,
                        amount=format_currency(sim_result.months[-1].cum_net, lang),
                    )
                )

            compliance = payload.get("compliance_summary", {})
            st.write(f"**{t('ui.reco.compliance', lang)}**")
            regulated = compliance.get("regulated_level", "none")
            st.write(
                f"- {t('ui.reco.regulated_level', lang)}: "
                f"{t(f'legal.regulated.{regulated}', lang)}"
            )
            required_kits = compliance.get("required_kits", [])
            if required_kits:
                kit_titles = [
                    t(kit_by_id[kit_id].title_key, lang)
                    for kit_id in required_kits
                    if kit_id in kit_by_id
                ]
                st.write(
                    f"- {t('ui.reco.required_kits', lang)}: {', '.join(kit_titles)}"
                )
            staleness = payload.get("staleness", {})
            if staleness.get("is_stale_force_check"):
                st.warning(t("ui.reco.stale_force", lang))
            elif staleness.get("is_stale_warn"):
                st.info(t("ui.reco.stale_warn", lang))

            if st.button(t("ui.reco.select", lang, variant_id=variant.variant_id)):
                st.session_state["selected_variant_id"] = variant.variant_id

from __future__ import annotations

import io
from pathlib import Path

import streamlit as st
import yaml

from money_map.core.evidence import load_registry
from money_map.core.model import UserProfile
from money_map.core.plan import build_plan
from money_map.core.recommend import recommend
from money_map.core.reviews import load_reviews
from money_map.core.workspace import get_workspace_paths
from money_map.i18n import t
from money_map.render.json import to_json
from money_map.render.md import render_checklist_md, render_plan_md
from money_map.ui.cache import appdata_signature, load_app_data_cached


def _result_payload(result, lang: str, appdata) -> dict:
    variant_by_id = {variant.variant_id: variant for variant in appdata.variants}
    ranked = []
    for item in result.ranked_variants:
        payload = item.model_dump() if hasattr(item, "model_dump") else item
        variant = variant_by_id[payload["variant_id"]]
        payload = {
            **payload,
            "title": t(variant.title_key, lang),
            "summary": t(variant.summary_key, lang),
            "pros": [t(reason, lang) for reason in payload.get("pros", [])],
            "cons": [t(reason, lang) for reason in payload.get("cons", [])],
            "blockers": [t(reason, lang) for reason in payload.get("blockers", [])],
            "assumptions": [t(reason, lang) for reason in payload.get("assumptions", [])],
        }
        ranked.append(payload)
    return {"ranked_variants": ranked, "diagnostics": result.diagnostics}


def render(data_dir: Path, lang: str, workspace: Path | None = None) -> None:
    st.header(t("ui.export.header", lang))
    profile: UserProfile = st.session_state.get("profile")
    if profile is None:
        st.info(t("ui.common.load_profile_first", lang))
        return

    if st.button(t("common.export", lang)):
        signature = appdata_signature(data_dir, workspace)
        appdata = load_app_data_cached(
            str(data_dir),
            profile.country_code,
            str(workspace) if workspace else None,
            signature,
        )
        reviews = None
        evidence_registry = None
        if workspace is not None:
            paths = get_workspace_paths(workspace)
            reviews = load_reviews(paths.reviews / "reviews.yaml")
            evidence_registry = load_registry(paths.evidence / "registry.yaml")
        result = recommend(
            profile,
            appdata,
            top_n=5,
            reviews=reviews,
            evidence_registry=evidence_registry,
        )
        top_item = result.ranked_variants[0]
        variant_id = (
            top_item.variant_id if hasattr(top_item, "variant_id") else top_item["variant_id"]
        )
        plan = build_plan(variant_id, profile, appdata)

        profile_bytes = yaml.safe_dump(profile.model_dump(), sort_keys=True).encode("utf-8")
        result_payload = _result_payload(result, lang, appdata)
        result_bytes = to_json(result_payload).encode("utf-8")
        plan_bytes = render_plan_md(plan, lang).encode("utf-8")
        checklist_bytes = render_checklist_md(plan.compliance_checklist, lang).encode("utf-8")

        st.download_button(
            t("ui.export.download_profile", lang),
            data=io.BytesIO(profile_bytes),
            file_name="profile.yaml",
        )
        st.download_button(
            t("ui.export.download_result", lang),
            data=io.BytesIO(result_bytes),
            file_name="result.json",
        )
        st.download_button(
            t("ui.export.download_plan", lang),
            data=io.BytesIO(plan_bytes),
            file_name="plan.md",
        )
        st.download_button(
            t("ui.export.download_checklist", lang),
            data=io.BytesIO(checklist_bytes),
            file_name="checklist.md",
        )

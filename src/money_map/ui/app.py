"""Streamlit UI for MoneyMap."""

from __future__ import annotations

import json
from collections import Counter
from uuid import uuid4

import streamlit as st
import yaml

from money_map.app.api import export_bundle
from money_map.core.graph import build_plan
from money_map.core.load import load_app_data
from money_map.core.recommend import recommend
from money_map.core.validate import validate
from money_map.render.plan_md import render_plan_md
from money_map.render.result_json import render_result_json
from money_map.ui.navigation import NAV_ITEMS, NAV_LABEL_BY_SLUG, resolve_page_from_query
from money_map.ui.projection_state import (
    compute_profile_hash,
    ensure_defaults,
    get_filters,
    get_plan_state,
    get_profile,
    get_recommendation_state,
    get_selection,
    set_filters,
    set_plan_state,
    set_profile,
    set_recommendation_state,
    set_selection,
)
from money_map.ui.theme import inject_global_theme
from money_map.ui.view_mode import get_view_mode, render_view_mode_control

DEFAULT_PROFILE = {
    "name": "Demo",
    "objective": "fastest_money",
    "language_level": "B1",
    "capital_eur": 300,
    "time_per_week": 15,
    "assets": ["laptop", "phone"],
    "location": "Berlin",
}

TAXONOMY_MECHANISMS = [f"M{i:02d}" for i in range(1, 15)]
CELLS = [f"cell_{i}" for i in range(1, 9)]


@st.cache_resource
def _get_app_data():
    return load_app_data()


@st.cache_data
def _get_validation() -> dict:
    report = validate(_get_app_data())
    return {
        "status": report.status,
        "fatals": report.fatals,
        "warns": report.warns,
        "dataset_version": report.dataset_version,
        "reviewed_at": report.reviewed_at,
        "stale": report.stale,
    }


def _render_filter_panel() -> dict:
    current = get_filters()
    filters = {
        "top_n": st.number_input("top_n", 1, 20, int(current.top_n)),
        "startability_window": st.number_input(
            "startability_window(days)", 1, 90, int(current.startability_window)
        ),
        "max_legal_friction": st.slider(
            "max_legal_friction", 0, 4, int(current.max_legal_friction)
        ),
        "allowed_legal_gates": st.multiselect(
            "allowed legal_gate",
            ["ok", "require_check", "registration", "license", "blocked"],
            default=current.allowed_legal_gates,
        ),
        "allowed_feasibility_status": st.multiselect(
            "allowed feasibility",
            ["feasible", "feasible_with_prep", "not_feasible"],
            default=current.allowed_feasibility_status,
        ),
        "max_time_to_first_money_days": st.number_input(
            "max time_to_first_money", 1, 365, int(current.max_time_to_first_money_days)
        ),
        "min_typical_net_month": st.number_input(
            "min typical_net_month", 0, 10000, int(current.min_typical_net_month)
        ),
        "compliance_mode": st.selectbox(
            "compliance_mode",
            ["include_with_prep", "exclude_if_requires_prep"],
            index=0 if current.compliance_mode == "include_with_prep" else 1,
        ),
        "include_tags": current.include_tags,
        "exclude_tags": current.exclude_tags,
        "max_risk": current.max_risk,
    }
    set_filters(filters)
    return filters


def _run_recommendations() -> None:
    profile = get_profile().payload
    filters = get_filters()
    app_data = _get_app_data()
    result = recommend(
        profile,
        app_data.variants,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        profile.get("objective", "fastest_money"),
        filters.__dict__,
        int(filters.top_n),
    )
    set_recommendation_state(result, compute_profile_hash(profile, filters))


def _ensure_plan() -> None:
    app_data = _get_app_data()
    selection = get_selection()
    if not selection.selected_variant_id:
        return
    variant = next(
        (v for v in app_data.variants if v.variant_id == selection.selected_variant_id), None
    )
    if not variant:
        return
    filters = get_filters()
    plan = build_plan(
        get_profile().payload,
        variant,
        app_data.rulepack,
        app_data.meta.staleness_policy,
        compliance_mode=filters.compliance_mode,
    )
    cache_key = f"{selection.selected_variant_id}:{filters.compliance_mode}"
    set_plan_state(plan, cache_key)


def run_app() -> None:
    ensure_defaults(DEFAULT_PROFILE)
    st.session_state.setdefault("ui_run_id", str(uuid4()))
    st.session_state.setdefault("page", "appdata")
    st.session_state.setdefault("theme_preset", "Light")
    st.session_state.setdefault("view_mode", "User")
    st.session_state.setdefault("page_initialized", False)

    page_slugs = [slug for _, slug in NAV_ITEMS]
    params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
    if not st.session_state.get("page_initialized", False):
        st.session_state["page"] = resolve_page_from_query(
            params, st.session_state.get("page", "appdata")
        )
        st.session_state["page_initialized"] = True
    if st.session_state["page"] not in page_slugs:
        st.session_state["page"] = page_slugs[0]

    inject_global_theme(st.session_state.get("theme_preset", "Light"))
    page_slug = st.sidebar.radio(
        "Navigate",
        page_slugs,
        format_func=lambda slug: NAV_LABEL_BY_SLUG.get(slug, slug),
        key="page",
    )
    if resolve_page_from_query(params, "") != page_slug:
        if hasattr(st, "query_params"):
            st.query_params["page"] = page_slug
    render_view_mode_control("sidebar")
    view_mode = get_view_mode()

    app_data = _get_app_data()
    report = _get_validation()

    if page_slug == "appdata":
        st.title("AppData")
        st.json(
            {
                "dataset_version": report["dataset_version"],
                "reviewed_at": report["reviewed_at"],
                "warnings": report["warns"],
                "variants": len(app_data.variants),
                "bridges": len(app_data.bridges),
                "taxonomy_entries": len({v.taxonomy_id for v in app_data.variants}),
                "rulepack_country": "DE",
            }
        )

    elif page_slug == "profile":
        st.title("UserProfile")
        profile = get_profile().payload
        profile["name"] = st.text_input("name", profile.get("name", ""))
        profile["location"] = st.text_input("location", profile.get("location", ""))
        profile["capital_eur"] = st.number_input(
            "capital_eur", 0, 100000, int(profile.get("capital_eur", 0))
        )
        profile["time_per_week"] = st.number_input(
            "time_per_week", 0, 80, int(profile.get("time_per_week", 0))
        )
        profile["objective"] = st.selectbox(
            "objective",
            ["fastest_money", "max_net"],
            index=0 if profile.get("objective") == "fastest_money" else 1,
        )
        set_profile(profile)

    elif page_slug == "variant":
        st.title("Variant")
        filters = _render_filter_panel()
        rows = []
        for v in app_data.variants:
            rows.append(
                {
                    "id": v.variant_id,
                    "title": v.title,
                    "taxonomy": v.taxonomy_id,
                    "cell": ",".join(v.cells),
                    "legal_gate": v.legal.get("legal_gate", "ok"),
                    "time_to_first_money": v.economics.get(
                        "time_to_first_money_days_range", [0, 0]
                    ),
                    "typical_net_month": v.economics.get("typical_net_month_eur_range", [0, 0]),
                }
            )
        st.dataframe(rows, use_container_width=True)
        selected = st.selectbox("select variant", [""] + [v.variant_id for v in app_data.variants])
        if selected:
            set_selection(selected, "variant-page")
            details = next(v for v in app_data.variants if v.variant_id == selected)
            st.subheader("Variant details")
            st.json(
                {
                    "feasibility": details.feasibility,
                    "economics": details.economics,
                    "legal": details.legal,
                }
            )
            if st.button("Build plan for selected"):
                st.session_state["page"] = "plan"
        st.caption(f"Mode: {view_mode}. Variant facts are read-only in User mode.")
        if filters["compliance_mode"] == "exclude_if_requires_prep":
            st.info("Variants with legal_gate != ok are filtered out in RecommendationResult.")

    elif page_slug == "taxonomy-cells":
        st.title("Taxonomy/Cells")
        st.write("Mechanisms", TAXONOMY_MECHANISMS)
        st.write("Cells", CELLS)
        taxonomy = st.selectbox("taxonomy", sorted({v.taxonomy_id for v in app_data.variants}))
        cell = st.selectbox("cell", sorted({c for v in app_data.variants for c in v.cells}))
        st.dataframe(
            [
                {"id": v.variant_id, "title": v.title}
                for v in app_data.variants
                if v.taxonomy_id == taxonomy and cell in v.cells
            ]
        )

    elif page_slug == "bridges-paths":
        st.title("Bridges/Paths")
        from_cell = st.selectbox(
            "from_cell", [""] + sorted({b.from_cell for b in app_data.bridges})
        )
        to_cell = st.selectbox("to_cell", [""] + sorted({b.to_cell for b in app_data.bridges}))
        bridges = [
            b
            for b in app_data.bridges
            if (not from_cell or b.from_cell == from_cell) and (not to_cell or b.to_cell == to_cell)
        ]
        st.dataframe(
            [
                {
                    "bridge_id": b.bridge_id,
                    "from": b.from_cell,
                    "to": b.to_cell,
                    "preconditions": "; ".join(b.preconditions),
                    "steps": "; ".join(b.steps),
                }
                for b in bridges
            ]
        )

    elif page_slug == "rulepack":
        st.title("RulePack")
        rp = app_data.rulepack
        st.json(
            {
                "reviewed_at": rp.reviewed_at,
                "staleness_policy": rp.staleness_policy.stale_after_days,
                "rules": [r.rule_id for r in rp.rules],
                "compliance_kits": rp.compliance_kits,
            }
        )
        if report["stale"]:
            st.warning("Rulepack stale: diagnostics and legal checks are more strict.")

    elif page_slug == "recommendations":
        st.title("RecommendationResult")
        _render_filter_panel()
        if st.button("Run recommendations"):
            _run_recommendations()
        result = get_recommendation_state().result
        if result is None:
            st.info("Run recommendations")
        else:
            for rec in result.ranked_variants:
                st.write(f"{rec.variant.variant_id}: {rec.variant.title}")
                st.caption(f"feasibility={rec.feasibility.status}; legal={rec.legal.legal_gate}")
                if st.button(
                    f"Select {rec.variant.variant_id}", key=f"rec-{rec.variant.variant_id}"
                ):
                    set_selection(rec.variant.variant_id, "recommendation")
            blocker_counts = Counter()
            for rec in result.ranked_variants:
                blocker_counts.update(rec.feasibility.blockers)
            if blocker_counts:
                st.warning(
                    "Top blockers: "
                    + ", ".join(f"{k}({v})" for k, v in blocker_counts.most_common(3))
                )
            if st.button("Quick fix: startable in 2 weeks"):
                f = get_filters().__dict__
                f["max_time_to_first_money_days"] = 14
                set_filters(f)
                _run_recommendations()

    elif page_slug == "plan":
        st.title("RoutePlan")
        selection = get_selection()
        if not selection.selected_variant_id:
            st.info("Select variant in RecommendationResult or Variant page.")
        else:
            result = get_recommendation_state().result
            filters = get_filters()
            if (
                filters.compliance_mode == "exclude_if_requires_prep"
                and result is not None
                and selection.selected_variant_id
                not in {r.variant.variant_id for r in result.ranked_variants}
            ):
                st.warning(
                    "selection no longer allowed by filters. Return to RecommendationResult."
                )
            if st.button("Build / Refresh plan"):
                _ensure_plan()
            plan = get_plan_state().route_plan
            if plan:
                st.write("Steps", [s.title for s in plan.steps])
                st.write("4-week plan", plan.week_plan)
                st.write("Compliance", plan.compliance)

    elif page_slug == "export":
        st.title("Exports")
        selection = get_selection()
        plan = get_plan_state().route_plan
        rec_state = get_recommendation_state().result
        if not selection.selected_variant_id or not plan or rec_state is None:
            st.info("Complete RecommendationResult + RoutePlan first.")
        else:
            selected_rec = next(
                (
                    r
                    for r in rec_state.ranked_variants
                    if r.variant.variant_id == selection.selected_variant_id
                ),
                None,
            )
            if selected_rec is None:
                st.warning("Selected variant is out of current recommendations.")
            else:
                profile = get_profile().payload
                result_payload = render_result_json(
                    profile,
                    selected_rec,
                    plan,
                    diagnostics=rec_state.diagnostics,
                    profile_hash=rec_state.profile_hash,
                    run_id=st.session_state.get("ui_run_id"),
                    applied_filters=get_filters().__dict__,
                )
                st.download_button("plan.md", render_plan_md(plan), "plan.md")
                st.download_button(
                    "result.json",
                    json.dumps(result_payload, ensure_ascii=False, indent=2),
                    "result.json",
                )
                st.download_button(
                    "profile.yaml",
                    yaml.safe_dump(profile, sort_keys=False, allow_unicode=True),
                    "profile.yaml",
                )
                if st.button("Generate export files"):
                    paths = export_bundle(
                        None,
                        selection.selected_variant_id,
                        out_dir="exports",
                        data_dir="data",
                        profile_data=profile,
                    )
                    st.success(str(paths))


if __name__ == "__main__":
    run_app()

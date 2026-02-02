"""Streamlit UI for MoneyMap walking skeleton."""

from __future__ import annotations

import json
from collections import Counter

import streamlit as st
import yaml

from money_map.app.api import export_bundle
from money_map.core.graph import build_plan
from money_map.core.load import load_app_data
from money_map.core.recommend import recommend
from money_map.core.validate import validate
from money_map.render.plan_md import render_plan_md
from money_map.render.result_json import render_result_json

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
    return build_plan(profile, variant, app_data.rulepack)


def run_app() -> None:
    _init_state()

    st.sidebar.title("MoneyMap")
    page = st.sidebar.radio(
        "Navigate",
        ["Data status", "Profile", "Recommendations", "Plan", "Export"],
    )

    if page == "Data status":
        st.header("Data status")
        report = _get_validation()
        st.metric("Dataset version", report["dataset_version"])
        st.metric("Reviewed at", report["reviewed_at"])
        st.metric("Status", report["status"])
        st.write(f"Stale: {report['stale']}")
        if report["fatals"]:
            st.error("Fatals: " + ", ".join(report["fatals"]))
        if report["warns"]:
            st.warning("Warnings: " + ", ".join(report["warns"]))

    elif page == "Profile":
        st.header("Profile")
        quick_mode = st.toggle("Quick mode", value=True)
        profile = st.session_state["profile"]

        profile["name"] = st.text_input("Name", value=profile["name"])
        profile["location"] = st.text_input("Location", value=profile["location"])
        profile["language_level"] = st.selectbox(
            "Language level",
            ["A1", "A2", "B1", "B2", "C1", "C2", "native"],
            index=2,
        )
        profile["capital_eur"] = st.number_input("Capital (EUR)", value=profile["capital_eur"])
        profile["time_per_week"] = st.number_input("Time per week", value=profile["time_per_week"])
        assets = st.text_input(
            "Assets (comma separated)",
            value=", ".join(profile["assets"]),
        )
        profile["assets"] = [item.strip() for item in assets.split(",") if item.strip()]

        if not quick_mode:
            objective_options = ["fastest_money", "max_net"]
            profile["objective"] = st.selectbox(
                "Objective",
                objective_options,
                index=objective_options.index(profile.get("objective", "fastest_money")),
            )

        st.session_state["profile"] = profile
        st.success("Profile ready" if profile["name"] else "Profile draft")

    elif page == "Recommendations":
        st.header("Recommendations")
        profile = st.session_state["profile"]
        objective_options = ["fastest_money", "max_net"]
        current_objective = profile.get("objective", "fastest_money")
        selected_objective = st.selectbox(
            "Objective preset",
            objective_options,
            index=objective_options.index(current_objective),
        )
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
                    f"Select {rec.variant.variant_id}", key=f"select-{rec.variant.variant_id}"
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

    elif page == "Plan":
        st.header("Plan")
        variant_id = st.session_state.get("selected_variant_id")
        if not variant_id:
            st.info("Select a variant in Recommendations.")
        else:
            profile = st.session_state["profile"]
            try:
                plan = _ensure_plan(profile, variant_id)
            except ValueError as exc:
                st.error(str(exc))
            else:
                last_result = st.session_state.get("last_recommendations")
                if last_result is not None:
                    selected = next(
                        (
                            rec
                            for rec in last_result.ranked_variants
                            if rec.variant.variant_id == variant_id
                        ),
                        None,
                    )
                else:
                    selected = None
                if plan.legal_gate != "ok" or (selected and selected.stale):
                    warnings = []
                    if plan.legal_gate != "ok":
                        warnings.append(f"Legal gate: {plan.legal_gate}")
                    if selected and selected.stale:
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

    elif page == "Export":
        st.header("Export")
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
                (r for r in recommendations.ranked_variants if r.variant.variant_id == variant_id),
                None,
            )
            result_payload = (
                render_result_json(profile, selected_rec, plan) if selected_rec else None
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
                except ValueError as exc:
                    st.error(str(exc))
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


if __name__ == "__main__":
    run_app()

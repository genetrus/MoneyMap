"""Streamlit UI for MoneyMap walking skeleton."""

from __future__ import annotations

import streamlit as st

from money_map.app.api import export_bundle, plan_variant, recommend_variants, validate_data


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
    st.session_state.setdefault("objective", "fastest_money")
    st.session_state.setdefault("filters", {"exclude_blocked": True})
    st.session_state.setdefault("selected_variant_id", "")
    st.session_state.setdefault("plan", None)
    st.session_state.setdefault("last_recommendations", None)


_init_state()

st.sidebar.title("MoneyMap")
page = st.sidebar.radio(
    "Navigate",
    ["Data status", "Profile", "Recommendations", "Plan", "Export"],
)


if page == "Data status":
    st.header("Data status")
    report = validate_data()
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
        ["A2", "B1", "B2", "C1", "C2", "native"],
        index=1,
    )
    profile["capital_eur"] = st.number_input("Capital (EUR)", value=profile["capital_eur"])
    profile["time_per_week"] = st.number_input("Time per week", value=profile["time_per_week"])
    assets = st.text_input(
        "Assets (comma separated)",
        value=", ".join(profile["assets"]),
    )
    profile["assets"] = [item.strip() for item in assets.split(",") if item.strip()]

    if not quick_mode:
        profile["objective"] = st.selectbox(
            "Objective",
            ["fastest_money", "max_net"],
            index=0,
        )

    st.session_state["profile"] = profile
    st.success("Profile ready" if profile["name"] else "Profile draft")

elif page == "Recommendations":
    st.header("Recommendations")
    st.session_state["objective"] = st.selectbox(
        "Objective preset", ["fastest_money", "max_net"], index=0
    )
    top_n = st.slider("Top N", min_value=1, max_value=5, value=3)
    max_time = st.number_input("Max time to first money (days)", value=60)
    st.session_state["filters"]["max_time_to_money_days"] = int(max_time)
    st.session_state["filters"]["exclude_blocked"] = st.checkbox("Exclude blocked", value=True)

    if st.button("Run recommendations"):
        profile = st.session_state["profile"]
        result = recommend_variants(
            profile_path=None,
            objective=st.session_state["objective"],
            filters=st.session_state["filters"],
            top_n=top_n,
            data_dir="data",
            profile_data=profile,
        )
        st.session_state["last_recommendations"] = result

    result = st.session_state.get("last_recommendations")
    if result is None:
        st.info("Run recommendations to see results.")
    elif not result.ranked_variants:
        st.warning("No results. Adjust filters and try again.")
    else:
        for rec in result.ranked_variants:
            st.subheader(rec.variant.title)
            st.caption(rec.variant.variant_id)
            st.write(
                f"Feasibility: {rec.feasibility.status} | "
                f"Legal: {rec.legal.legal_gate}"
            )
            st.write("Why: " + "; ".join(rec.pros))
            if rec.cons:
                st.write("Concerns: " + "; ".join(rec.cons))
            if st.button(f"Select {rec.variant.variant_id}", key=f"select-{rec.variant.variant_id}"):
                st.session_state["selected_variant_id"] = rec.variant.variant_id

        st.subheader("Reality Check")
        top_blockers = []
        for rec in result.ranked_variants:
            top_blockers.extend(rec.feasibility.blockers)
        top_blockers = top_blockers[:3]
        if top_blockers:
            st.warning("Top blockers: " + ", ".join(top_blockers))
        if st.button("Focus on fastest money"):
            st.session_state["objective"] = "fastest_money"
            st.session_state["filters"]["max_time_to_money_days"] = 30
        if st.button("Reduce legal friction"):
            st.session_state["filters"]["exclude_blocked"] = True

elif page == "Plan":
    st.header("Plan")
    variant_id = st.session_state.get("selected_variant_id")
    if not variant_id:
        st.info("Select a variant in Recommendations.")
    else:
        profile = st.session_state["profile"]
        plan = plan_variant(
            profile_path=None,
            variant_id=variant_id,
            data_dir="data",
            profile_data=profile,
        )
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
    if not variant_id:
        st.info("Select a variant and generate a plan first.")
    else:
        if st.button("Export"):
            profile = st.session_state["profile"]
            paths = export_bundle(
                profile_path=None,
                variant_id=variant_id,
                out_dir="exports",
                data_dir="data",
                profile_data=profile,
            )
            st.success("Export completed")
            st.write(paths)

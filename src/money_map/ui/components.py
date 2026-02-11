"""Shared shell and design-system components for MoneyMap Streamlit UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from money_map.ui.status_tokens import (
    confidence_dots,
    get_feasibility_token,
    get_legal_token,
    get_staleness_token,
)


BADGE_CLASS_BY_STALENESS = {
    "ok": "badge-valid",
    "warn": "badge-stale",
    "hard": "badge-invalid",
}


def _badge(label: str, value: str, *, css_class: str = "badge-stale") -> str:
    return f'<span class="status-badge {css_class}"><strong>{label}:</strong> {value}</span>'


def render_badge_set(
    *,
    feasibility: str | None = None,
    legal_gate: str | None = None,
    staleness: str | None = None,
    confidence: Any | None = None,
) -> None:
    chips: list[str] = []
    if feasibility is not None:
        text, css = get_feasibility_token(feasibility)
        chips.append(_badge("Feasibility", text, css_class=css))
    if legal_gate is not None:
        text, css = get_legal_token(legal_gate)
        chips.append(_badge("Legal", text, css_class=css))
    if staleness is not None:
        text, css = get_staleness_token(staleness)
        chips.append(_badge("Staleness", text, css_class=css))
    if confidence is not None:
        chips.append(_badge("Confidence", confidence_dots(confidence), css_class="badge-stale"))

    if chips:
        st.markdown(
            '<div class="mm-badge-set">' + "".join(chips) + "</div>",
            unsafe_allow_html=True,
        )


def render_kpi_grid(items: list[dict[str, str]]) -> None:
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            status = item.get("status", "")
            status_html = ""
            if status:
                status_text, status_class = get_staleness_token(status)
                status_html = _badge("Status", status_text, css_class=status_class)

            subtext = item.get("subtext")
            subtext_html = f'<div class="kpi-subtext">{subtext}</div>' if subtext else ""
            st.markdown(
                f"""
                <div class="kpi-card">
                  <div class="kpi-label">{item.get("label", "")}</div>
                  <div class="kpi-value">{item.get("value", "")}</div>
                  {status_html}
                  {subtext_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_header_bar(
    *,
    country: str,
    dataset_version: str,
    reviewed_at: str,
    staleness_level: str,
    view_mode: str,
) -> None:
    staleness = staleness_level.upper()
    badge_class = BADGE_CLASS_BY_STALENESS.get(staleness.lower(), "badge-stale")
    badges = "".join(
        [
            _badge("Country", country, css_class="badge-valid"),
            _badge("Dataset", dataset_version, css_class="badge-valid"),
            _badge("Reviewed", reviewed_at, css_class="badge-stale"),
            _badge("Staleness", staleness, css_class=badge_class),
            _badge("Mode", view_mode, css_class="badge-stale"),
        ]
    )
    st.markdown(
        f"""
        <div class="mm-shell-header">
          <div class="mm-shell-title">Money Map</div>
          <div class="mm-shell-badges">{badges}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_context_bar(*, page: str, subview: str | None, selected_ids: dict[str, str]) -> None:
    crumbs = [page]
    if subview:
        crumbs.append(subview)

    focus = [f"{k}: {v}" for k, v in selected_ids.items() if v]
    focus_text = " · ".join(focus) if focus else "No pinned selection"
    st.markdown(
        f"""
        <div class="mm-context-bar">
          <div><strong>Context:</strong> {" / ".join(crumbs)}</div>
          <div class="mm-context-focus">{focus_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_detail_drawer(selected_ids: dict[str, str], *, page_slug: str) -> None:
    with st.expander("Detail Drawer", expanded=False):
        has_selection = any(selected_ids.values())
        if not has_selection:
            st.caption(
                "No entity selected yet. Pick Cell/Taxonomy/Variant/Bridge/Path to pin context."
            )
            return

        st.write("Pinned selection")
        for key, value in selected_ids.items():
            if value:
                st.write(f"- **{key}**: `{value}`")

        st.write("Cross-links")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Open in Explore", key=f"drawer-open-explore-{page_slug}"):
                st.session_state["page"] = "explore"
                st.rerun()
        with col2:
            if st.button("Filter Recommendations", key=f"drawer-open-rec-{page_slug}"):
                st.session_state["page"] = "recommendations"
                st.rerun()
        with col3:
            disabled = not bool(selected_ids.get("variant"))
            if st.button("Build Plan", key=f"drawer-open-plan-{page_slug}", disabled=disabled):
                st.session_state["selected_variant_id"] = selected_ids.get("variant", "")
                st.session_state["page"] = "plan"
                st.rerun()


def render_graph_fallback(
    *,
    title: str,
    graphviz_dot: str,
    nodes_rows: list[dict[str, str]],
    edges_rows: list[dict[str, str]],
    key_prefix: str,
    interactive_available: bool = False,
) -> None:
    st.markdown(f"**{title}**")
    if not interactive_available:
        st.info("Interactive view unavailable, fallback applied.")

    try:
        st.graphviz_chart(graphviz_dot, use_container_width=True)
    except Exception:
        st.warning("Graphviz render failed, table fallback applied.")

    with st.expander("Graph fallback: list/table", expanded=False):
        if nodes_rows:
            st.write("Nodes")
            st.dataframe(nodes_rows, use_container_width=True)
        if edges_rows:
            st.write("Edges")
            st.dataframe(edges_rows, use_container_width=True)

        node_ids = [row.get("id", "") for row in nodes_rows if row.get("id")]
        edge_ids = [row.get("id", "") for row in edges_rows if row.get("id")]
        selected_node = st.selectbox(
            "Select node",
            [""] + node_ids,
            key=f"{key_prefix}-fallback-node",
            format_func=lambda value: value or "none",
        )
        selected_edge = st.selectbox(
            "Select edge",
            [""] + edge_ids,
            key=f"{key_prefix}-fallback-edge",
            format_func=lambda value: value or "none",
        )
        if selected_node:
            st.caption(f"Selected node: {selected_node}")
        if selected_edge:
            st.caption(f"Selected edge: {selected_edge}")


def selected_ids_from_state(state: dict[str, Any]) -> dict[str, str]:
    return {
        "cell": str(state.get("selected_cell_id") or state.get("explore_selected_cell") or ""),
        "taxonomy": str(
            state.get("selected_taxonomy_id") or state.get("explore_selected_taxonomy") or ""
        ),
        "variant": str(state.get("selected_variant_id") or ""),
        "bridge": str(
            state.get("selected_bridge_id") or state.get("explore_selected_bridge") or ""
        ),
        "path": str(state.get("selected_path_id") or ""),
    }

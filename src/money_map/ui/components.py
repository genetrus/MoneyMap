"""Shared shell and design-system components for MoneyMap Streamlit UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from money_map.ui.copy import copy_text
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
    focus_text = (
        " · ".join(focus)
        if focus
        else copy_text("components.context_bar.no_pinned_selection", "No pinned selection")
    )
    context_prefix = copy_text("components.context_bar.context_prefix", "Context")
    st.markdown(
        f"""
        <div class="mm-context-bar">
          <div><strong>{context_prefix}:</strong> {" / ".join(crumbs)}</div>
          <div class="mm-context-focus">{focus_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button(
            copy_text("components.context_bar.staleness_badge", "Staleness"),
            key="context-open-data-status",
            help=copy_text(
                "components.context_bar.staleness_effect",
                "Откроет Data status и покажет риски устаревания данных.",
            ),
            use_container_width=True,
        ):
            st.session_state["page"] = "data-status"
            st.rerun()
    with c2:
        if st.button(
            copy_text("components.context_bar.profile_badge", "Profile"),
            key="context-open-profile",
            help=copy_text(
                "components.context_bar.profile_effect",
                "Откроет Profile для исправления ограничений/обязательных полей.",
            ),
            use_container_width=True,
        ):
            st.session_state["page"] = "profile"
            st.rerun()
    with c3:
        if st.button(
            copy_text("components.context_bar.selected_badge", "Selected"),
            key="context-open-drawer",
            help=copy_text(
                "components.context_bar.selected_effect",
                "Откроет Detail Drawer для выбранной сущности и быстрых действий.",
            ),
            use_container_width=True,
        ):
            st.session_state["open_detail_drawer"] = True
            st.rerun()


def render_guide_panel(*, runtime: dict[str, Any], current_page_slug: str) -> None:
    current_step = runtime.get("current_step") or {}
    blockers = runtime.get("blockers") or []
    primary_action = runtime.get("primary_action") or {}
    resolver = runtime.get("blockers_resolver") or {}

    st.markdown(f"### {copy_text('guide_panel.title', 'Guide panel')}")
    st.caption(str(current_step.get("goal") or ""))

    do_now = current_step.get("do_now") or []
    if do_now:
        st.markdown(f"**{copy_text('guide_panel.do_now', 'Сделай сейчас')}**")
        for item in do_now:
            st.markdown(f"- {item}")

    if blockers:
        st.warning(copy_text("guided.blocked_title", "Шаг заблокирован:"))
        for blocker in blockers:
            st.caption(f"• {blocker}")
        if st.button(
            copy_text("guided.resolve_cta", "Показать где исправить"),
            key=f"guide-panel-resolve-{current_step.get('id', current_page_slug)}",
            use_container_width=True,
        ):
            focus_page = str(resolver.get("focus_page") or primary_action.get("target_page") or "")
            st.session_state["page"] = focus_page
            st.session_state["guide_highlight_fields"] = resolver.get("highlight_fields", [])
            st.rerun()

    label = str(primary_action.get("label") or "Continue")
    target_page = str(primary_action.get("target_page") or current_page_slug)
    if st.button(
        label,
        key=f"guide-panel-primary-{current_step.get('id', current_page_slug)}",
        disabled=bool(primary_action.get("disabled")),
        help=copy_text(
            "guide_panel.primary_effect",
            "Перейдёт на следующий шаг. Если шаг заблокирован — сначала исправь блокеры.",
        ),
        use_container_width=True,
    ):
        st.session_state["page"] = target_page
        st.rerun()


def render_detail_drawer(
    selected_ids: dict[str, str],
    *,
    page_slug: str,
    expanded: bool = False,
) -> None:
    with st.expander(
        copy_text("components.detail_drawer.title", "Detail Drawer"),
        expanded=expanded,
    ):
        has_selection = any(selected_ids.values())
        if not has_selection:
            st.caption(
                copy_text("components.detail_drawer.no_entity_selected", "No entity selected yet.")
            )
            return

        st.write(copy_text("components.detail_drawer.pinned_selection", "Pinned selection"))
        for key, value in selected_ids.items():
            if value:
                st.write(f"- **{key}**: `{value}`")

        st.write(copy_text("components.detail_drawer.cross_links", "Cross-links"))
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(
                copy_text("components.detail_drawer.open_explore", "Open in Explore"),
                key=f"drawer-open-explore-{page_slug}",
                help=copy_text(
                    "components.detail_drawer.open_explore_effect",
                    "Откроет Explore и сохранит текущий фокус.",
                ),
            ):
                st.session_state["page"] = "explore"
                st.rerun()
        with col2:
            if st.button(
                copy_text(
                    "components.detail_drawer.filter_recommendations", "Filter Recommendations"
                ),
                key=f"drawer-open-rec-{page_slug}",
                help=copy_text(
                    "components.detail_drawer.filter_recommendations_effect",
                    "Перейдёт в Recommendations и применит контекст выбора как фильтр.",
                ),
            ):
                st.session_state["page"] = "recommendations"
                st.rerun()
        with col3:
            disabled = not bool(selected_ids.get("variant"))
            if st.button(
                copy_text("components.detail_drawer.build_plan", "Build Plan"),
                key=f"drawer-open-plan-{page_slug}",
                disabled=disabled,
                help=copy_text(
                    "components.detail_drawer.build_plan_effect",
                    "Сохранит выбранный вариант и откроет Plan.",
                ),
            ):
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
        st.info(
            copy_text(
                "components.graph_fallback.interactive_unavailable",
                "Interactive view unavailable, fallback applied.",
            )
        )

    try:
        st.graphviz_chart(graphviz_dot, use_container_width=True)
    except Exception:
        st.warning(
            copy_text(
                "components.graph_fallback.render_failed",
                "Graphviz render failed, table fallback applied.",
            )
        )

    with st.expander(
        copy_text("components.graph_fallback.expander_title", "Graph fallback: list/table"),
        expanded=False,
    ):
        if nodes_rows:
            st.write(copy_text("components.graph_fallback.nodes_title", "Nodes"))
            st.dataframe(nodes_rows, use_container_width=True)
        if edges_rows:
            st.write(copy_text("components.graph_fallback.edges_title", "Edges"))
            st.dataframe(edges_rows, use_container_width=True)

        node_ids = [row.get("id", "") for row in nodes_rows if row.get("id")]
        edge_ids = [row.get("id", "") for row in edges_rows if row.get("id")]
        selected_node = st.selectbox(
            copy_text("components.graph_fallback.select_node", "Select node"),
            [""] + node_ids,
            key=f"{key_prefix}-fallback-node",
            format_func=lambda value: value or copy_text("components.graph_fallback.none", "none"),
        )
        selected_edge = st.selectbox(
            copy_text("components.graph_fallback.select_edge", "Select edge"),
            [""] + edge_ids,
            key=f"{key_prefix}-fallback-edge",
            format_func=lambda value: value or copy_text("components.graph_fallback.none", "none"),
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

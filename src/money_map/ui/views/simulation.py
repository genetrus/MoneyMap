from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from money_map.core.load import load_app_data
from money_map.core.simulate import simulate_variant
from money_map.i18n import t
from money_map.i18n.locale import format_currency


def render(data_dir: Path, lang: str, workspace: Path | None = None) -> None:
    st.header(t("nav.simulation", lang))
    profile = st.session_state.get("profile")
    if profile is None:
        st.info(t("ui.common.load_profile_first", lang))
        return

    appdata = load_app_data(data_dir, workspace=workspace)
    variant_ids = [variant.variant_id for variant in appdata.variants]
    selected_variant = st.selectbox(t("ui.simulation.variant", lang), options=variant_ids)
    months = st.number_input(t("ui.simulation.months", lang), min_value=1, max_value=36, value=6)

    variant = next(item for item in appdata.variants if item.variant_id == selected_variant)
    result = simulate_variant(
        profile,
        variant,
        appdata.presets[0] if appdata.presets else None,
        int(months),
        date.today(),
    )
    rows = [
        {
            "month": row.month_label,
            "net": row.net,
            "cum_net": row.cum_net,
        }
        for row in result.months
    ]
    try:
        import pandas as pd  # type: ignore

        st.line_chart(pd.DataFrame(rows).set_index("month"))
    except ImportError:
        st.line_chart(rows)

    table_rows = [
        {
            t("sim.table.month", lang): row.month_label,
            t("sim.table.revenue", lang): format_currency(row.revenue, lang),
            t("sim.table.opex", lang): format_currency(row.opex, lang),
            t("sim.table.capex", lang): format_currency(row.capex, lang),
            t("sim.table.net", lang): format_currency(row.net, lang),
            t("sim.table.cum_net", lang): format_currency(row.cum_net, lang),
        }
        for row in result.months
    ]
    st.dataframe(table_rows, use_container_width=True)

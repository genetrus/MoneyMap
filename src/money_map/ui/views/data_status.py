from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import streamlit as st

from money_map.core.load import load_app_data
from money_map.core.validate import validate_app_data
from money_map.i18n import t
from money_map.i18n.locale import format_date, format_int


def _to_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.today()


def render(data_dir: Path, lang: str) -> None:
    st.header(t("nav.data_status", lang))
    appdata = load_app_data(data_dir)
    st.write(f"{t('ui.data_status.dataset_version', lang)}: {appdata.meta.dataset_version}")
    st.write(
        f"{t('ui.data_status.reviewed_at', lang)}: "
        f"{format_date(appdata.meta.reviewed_at, lang)}"
    )

    days = (date.today() - _to_date(appdata.meta.reviewed_at)).days
    if days > appdata.meta.staleness_policy.warn_after_days:
        st.warning(t("ui.data_status.stale_warning", lang, days=format_int(days, lang)))

    if st.button(t("common.run_validate", lang)):
        fatals, warns = validate_app_data(data_dir)
        st.write(
            {
                "fatals": [t(key, lang, **params) for key, params in fatals],
                "warns": [t(key, lang, **params) for key, params in warns],
            }
        )

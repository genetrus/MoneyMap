from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from money_map.core.reviews import ReviewEntry, load_reviews, save_reviews
from money_map.core.workspace import get_workspace_paths
from money_map.i18n import t


def render(data_dir: Path, lang: str, workspace: Path | None = None) -> None:
    st.header(t("nav.reviews", lang))
    if workspace is None:
        st.info(t("ui.review.no_workspace", lang))
        return
    paths = get_workspace_paths(workspace)
    reviews = load_reviews(paths.reviews / "reviews.yaml")

    rows = [
        {
            t("ui.review.entity", lang): entry.entity_ref,
            t("ui.review.status", lang): entry.status,
            t("ui.review.verified_at", lang): entry.verified_at or "-",
            t("ui.review.reviewer", lang): entry.reviewer or "-",
        }
        for entry in sorted(reviews.entries, key=lambda item: item.entity_ref)
    ]
    st.dataframe(rows, use_container_width=True)

    st.subheader(t("ui.review.update", lang))
    entity_ref = st.text_input(t("ui.review.entity", lang), value="")
    status = st.selectbox(
        t("ui.review.status", lang),
        options=["unverified", "verified", "needs_update", "deprecated"],
    )
    reviewer = st.text_input(t("ui.review.reviewer", lang), value="")
    note = st.text_area(t("ui.review.note", lang), value="")
    if st.button(t("ui.review.save", lang)):
        entry = next(
            (item for item in reviews.entries if item.entity_ref == entity_ref),
            None,
        )
        if entry is None:
            entry = ReviewEntry(entity_ref=entity_ref)
            reviews.entries.append(entry)
        entry.status = status
        entry.reviewer = reviewer or None
        if status == "verified":
            entry.verified_at = date.today().isoformat()
        if note:
            entry.notes.append(note)
        reviews.reviewed_at = date.today().isoformat()
        save_reviews(paths.reviews / "reviews.yaml", reviews)
        st.success(t("ui.review.saved", lang))

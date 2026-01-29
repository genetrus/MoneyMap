from __future__ import annotations

from pathlib import Path

import streamlit as st

from money_map.core.evidence import add_file_evidence, add_note_evidence, load_registry, validate_registry
from money_map.core.workspace import get_workspace_paths
from money_map.i18n import t


def render(data_dir: Path, lang: str, workspace: Path | None = None) -> None:
    st.header(t("nav.evidence", lang))
    if workspace is None:
        st.info(t("ui.evidence.no_workspace", lang))
        return
    paths = get_workspace_paths(workspace)
    registry = load_registry(paths.evidence / "registry.yaml")

    rows = []
    for item in sorted(registry.items, key=lambda entry: entry.evidence_id):
        rows.append(
            {
                t("ui.evidence.id", lang): item.evidence_id,
                t("ui.evidence.type", lang): item.type,
                t("ui.evidence.title", lang): item.title or item.title_key or "-",
                t("ui.evidence.related", lang): ", ".join(item.related_entities),
            }
        )
    st.dataframe(rows, use_container_width=True)

    st.subheader(t("ui.evidence.add_note", lang))
    evidence_id = st.text_input(t("ui.evidence.id", lang), value="")
    note = st.text_area(t("ui.evidence.note", lang), value="")
    if st.button(t("ui.evidence.add", lang)):
        if evidence_id and note:
            add_note_evidence(workspace, evidence_id, note)
            st.success(t("ui.evidence.added", lang))

    st.subheader(t("ui.evidence.add_file", lang))
    file_upload = st.file_uploader(t("ui.evidence.file", lang))
    file_id = st.text_input(t("ui.evidence.file_id", lang), value="")
    if st.button(t("ui.evidence.upload", lang)):
        if file_upload and file_id:
            temp_path = paths.evidence_files / file_upload.name
            temp_path.write_bytes(file_upload.read())
            add_file_evidence(workspace, temp_path, file_id, force=True)
            st.success(t("ui.evidence.added", lang))

    if st.button(t("ui.evidence.validate", lang)):
        fatals, warns = validate_registry(workspace)
        if fatals:
            st.error([t(key, lang, **params) for key, params in fatals])
        if warns:
            st.warning([t(key, lang, **params) for key, params in warns])
        if not fatals and not warns:
            st.success(t("ui.evidence.valid", lang))

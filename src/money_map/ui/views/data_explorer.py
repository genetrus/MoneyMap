from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from money_map.core.evidence import load_registry
from money_map.core.load import load_yaml
from money_map.core.validate import REQUIRED_FILES, validate_app_data
from money_map.core.workspace import detect_workspace_conflicts, get_workspace_paths
from money_map.i18n import t
from money_map.i18n.locale import format_int
from money_map.i18n.audit import audit_i18n
from money_map.ui.cache import appdata_signature, load_app_data_cached
from money_map.core.rulepack_authoring import lint_rulepack, scaffold_rulepack, validate_rulepack_structure


def _entity_options(appdata) -> dict[str, list]:
    return {
        "taxonomy": appdata.taxonomy,
        "cells": appdata.cells,
        "variants": appdata.variants,
        "skills": appdata.skills,
        "assets": appdata.assets,
        "constraints": appdata.constraints,
        "objectives": appdata.objectives,
        "presets": appdata.presets,
        "risks": appdata.risks,
        "rulepacks": list(appdata.rulepacks.values()),
    }


def _entity_id(entity, key: str) -> str:
    if hasattr(entity, key):
        return getattr(entity, key)
    return entity.get(key, "")


def _serialize(entity) -> str:
    if hasattr(entity, "model_dump"):
        return json.dumps(entity.model_dump(), indent=2, ensure_ascii=False, default=str)
    return json.dumps(entity, indent=2, ensure_ascii=False, default=str)


def render(data_dir: Path, lang: str, workspace: Path | None = None) -> None:
    st.header(t("ui.data_explorer.header", lang))

    signature = appdata_signature(data_dir, workspace)
    appdata = load_app_data_cached(
        str(data_dir), "DE", str(workspace) if workspace else None, signature
    )

    tabs = [
        t("ui.data_explorer.tab_entities", lang),
        t("ui.data_explorer.tab_rulepacks", lang),
    ]
    if workspace is not None:
        tabs.extend(
            [t("ui.data_explorer.tab_evidence", lang), t("ui.data_explorer.tab_conflicts", lang)]
        )
    tab_entities, tab_rulepacks, *rest = st.tabs(tabs)

    with tab_entities:
        st.subheader(t("ui.data_explorer.files_header", lang))
        file_rows = []
        counts = {
            "taxonomy.yaml": len(appdata.taxonomy),
            "cells.yaml": len(appdata.cells),
            "variants.yaml": len(appdata.variants),
            "bridges.yaml": len(load_yaml(data_dir / "bridges.yaml") or []),
            "knowledge/skills.yaml": len(appdata.skills),
            "knowledge/assets.yaml": len(appdata.assets),
            "knowledge/constraints.yaml": len(appdata.constraints),
            "knowledge/objectives.yaml": len(appdata.objectives),
            "presets.yaml": len(appdata.presets),
            "knowledge/risks.yaml": len(appdata.risks),
            "rulepacks": len(appdata.rulepacks),
        }
        for rel in REQUIRED_FILES:
            path = data_dir / rel
            file_rows.append(
                {
                    t("ui.data_explorer.file", lang): rel,
                    t("ui.data_explorer.exists", lang): path.exists(),
                    t("ui.data_explorer.count", lang): format_int(
                        counts.get(rel, 0), lang
                    ),
                }
            )
        file_rows.append(
            {
                t("ui.data_explorer.file", lang): "rulepacks/",
                t("ui.data_explorer.exists", lang): (data_dir / "rulepacks").exists(),
                t("ui.data_explorer.count", lang): format_int(counts["rulepacks"], lang),
            }
        )
        st.dataframe(file_rows, use_container_width=True)

        st.subheader(t("ui.data_explorer.validation_header", lang))
        if st.button(t("ui.data_explorer.run_validate", lang)):
            fatals, warns = validate_app_data(data_dir, workspace=workspace)
            st.write(
                f"{t('ui.data_explorer.validation_fatals', lang)}: {len(fatals)} | "
                f"{t('ui.data_explorer.validation_warns', lang)}: {len(warns)}"
            )
            if fatals:
                st.error([t(key, lang, **params) for key, params in fatals])
            if warns:
                st.warning([t(key, lang, **params) for key, params in warns])

        st.subheader(t("ui.data_explorer.i18n_header", lang))
        if st.button(t("ui.data_explorer.run_audit", lang)):
            fatals, warns = audit_i18n(data_dir)
            st.write(
                f"{t('ui.data_explorer.validation_fatals', lang)}: {len(fatals)} | "
                f"{t('ui.data_explorer.validation_warns', lang)}: {len(warns)}"
            )
            if fatals:
                st.error([f"{item.lang}: {item.key}" for item in fatals])
            if warns:
                st.warning([f"{item.lang}: {item.key}" for item in warns])

        st.subheader(t("ui.data_explorer.entities_header", lang))
        entities = _entity_options(appdata)
        entity_type = st.selectbox(
            t("ui.data_explorer.entity_type", lang), options=list(entities.keys())
        )
        items = entities[entity_type]
        id_key = {
            "taxonomy": "taxonomy_id",
            "cells": "cell_id",
            "variants": "variant_id",
            "skills": "skill_id",
            "assets": "asset_id",
            "constraints": "constraint_id",
            "objectives": "objective_id",
            "presets": "preset_id",
            "risks": "risk_id",
            "rulepacks": "country_code",
        }[entity_type]
        options = [_entity_id(item, id_key) for item in items]
        selected = st.selectbox(t("ui.data_explorer.entity_id", lang), options=options)
        selected_item = next(
            (item for item in items if _entity_id(item, id_key) == selected), None
        )
        if selected_item is not None:
            st.subheader(t("ui.data_explorer.entity_details", lang))
            st.json(json.loads(_serialize(selected_item)))

    with tab_rulepacks:
        st.subheader(t("ui.data_explorer.rulepacks_header", lang))
        country = st.selectbox(
            t("ui.data_explorer.rulepack_country", lang),
            options=sorted(appdata.rulepacks.keys()),
        )
        rulepack = appdata.rulepacks[country]
        st.write(f"**{t('ui.data_explorer.kits_header', lang)}**")
        for kit in rulepack.compliance_kits:
            st.write(f"- {t(kit.title_key, lang)} ({kit.kit_id})")
        st.write(f"**{t('ui.data_explorer.rules_header', lang)}**")
        for rule in rulepack.rules:
            st.write(f"- {t(rule.title_key, lang)} ({rule.rule_id})")

        st.subheader(t("ui.data_explorer.rulepack_authoring_header", lang))
        author_country = st.selectbox(
            t("ui.data_explorer.rulepack_authoring_country", lang),
            options=sorted(appdata.rulepacks.keys()),
            key="rulepack_authoring_country",
        )
        author_rulepack = appdata.rulepacks[author_country]
        if st.button(t("ui.data_explorer.rulepack_authoring_validate", lang)):
            issues = validate_rulepack_structure(
                author_rulepack.model_dump()
                if hasattr(author_rulepack, "model_dump")
                else author_rulepack
            )
            if issues:
                st.error([t(issue.key, lang, **issue.params) for issue in issues])
            else:
                st.success(t("ui.data_explorer.rulepack_authoring_valid", lang))
        if st.button(t("ui.data_explorer.rulepack_authoring_lint", lang)):
            warnings = lint_rulepack(
                author_rulepack.model_dump()
                if hasattr(author_rulepack, "model_dump")
                else author_rulepack
            )
            if warnings:
                st.warning([t(item.key, lang, **item.params) for item in warnings])
            else:
                st.success(t("ui.data_explorer.rulepack_authoring_clean", lang))
        if workspace is not None:
            if st.button(t("ui.data_explorer.rulepack_authoring_scaffold", lang)):
                out_path = get_workspace_paths(workspace).overlay_rulepacks / f"{author_country}.yaml"
                scaffold_rulepack(author_country, out_path, placeholder=True)
                st.success(
                    t(
                        "ui.data_explorer.rulepack_authoring_scaffolded",
                        lang,
                        path=str(out_path),
                    )
                )
        else:
            st.info(t("ui.data_explorer.rulepack_authoring_workspace_required", lang))

    if rest:
        tab_evidence = rest[0]
        with tab_evidence:
            st.subheader(t("ui.data_explorer.evidence_header", lang))
            if workspace is None:
                st.info(t("ui.evidence.no_workspace", lang))
                return
            registry = load_registry(get_workspace_paths(workspace).evidence / "registry.yaml")
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

        if len(rest) > 1:
            tab_conflicts = rest[1]
            with tab_conflicts:
                st.subheader(t("ui.data_explorer.conflicts_header", lang))
                conflicts = detect_workspace_conflicts(data_dir, workspace)
                if not conflicts:
                    st.success(t("ui.data_explorer.conflicts_none", lang))
                else:
                    rows = []
                    for item in conflicts:
                        rows.append(
                            {
                                t("ui.data_explorer.conflict_entity", lang): item.entity_ref,
                                t("ui.data_explorer.conflict_type", lang): t(
                                    f"conflict.{item.conflict_type}", lang
                                ),
                                t("ui.data_explorer.conflict_action", lang): t(
                                    f"conflict.action.{item.suggested_action}", lang
                                ),
                            }
                        )
                    st.dataframe(rows, use_container_width=True)

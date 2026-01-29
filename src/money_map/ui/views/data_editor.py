from __future__ import annotations

import difflib
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

from money_map.core.load import _safe_load_basic
from money_map.core.model import UserProfile
from money_map.core.validate import validate_app_data
from money_map.core.yaml_utils import dump_yaml, normalize_data
from money_map.i18n import t
from money_map.i18n.locale import format_date


def _allowed_roots(data_dir: Path) -> list[Path]:
    return [data_dir.resolve(), (data_dir.parent / "profiles").resolve()]


def _is_allowed(path: Path, roots: list[Path]) -> bool:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _list_yaml_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for ext in ("*.yaml", "*.yml"):
            files.extend(sorted(root.glob(f"**/{ext}")))
    return sorted(set(files))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_yaml(text: str) -> Any:
    if yaml:
        return yaml.safe_load(text)
    return _safe_load_basic(text)


def _summarize(parsed: Any) -> dict[str, Any]:
    if parsed is None:
        return {"type": "empty"}
    if isinstance(parsed, list):
        summary: dict[str, Any] = {"type": "list", "count": len(parsed)}
        if parsed and isinstance(parsed[0], dict):
            id_keys = [key for key in parsed[0].keys() if key.endswith("_id")]
            if id_keys:
                key = id_keys[0]
                summary["id_key"] = key
                summary["sample_ids"] = [item.get(key) for item in parsed[:5]]
        return summary
    if isinstance(parsed, dict):
        return {"type": "mapping", "keys": list(parsed.keys())[:10]}
    return {"type": type(parsed).__name__}


def _validate_profile(parsed: Any) -> tuple[bool, list[str]]:
    try:
        UserProfile.model_validate(parsed or {})
    except Exception as exc:  # pragma: no cover - safety
        return False, [str(exc)]
    return True, []


def _validate_data_dir(
    data_dir: Path, rel_path: Path, text: str, lang: str
) -> tuple[bool, list[str]]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir) / "data"
        shutil.copytree(data_dir, temp_root, dirs_exist_ok=True)
        temp_file = temp_root / rel_path
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text(text, encoding="utf-8")
        fatals, warns = validate_app_data(temp_root, strict=True)
        messages = [t(key, lang, **params) for key, params in fatals + warns]
        return (not fatals), messages


def _validate_draft(
    path: Path, data_dir: Path, text: str, lang: str
) -> tuple[bool, list[str]]:
    try:
        parsed = _parse_yaml(text)
    except Exception as exc:  # pragma: no cover - safety
        return False, [str(exc)]

    roots = _allowed_roots(data_dir)
    if path.resolve().is_relative_to(roots[1]):
        return _validate_profile(parsed)
    rel_path = path.resolve().relative_to(data_dir.resolve())
    return _validate_data_dir(data_dir, rel_path, text, lang)


def _safe_write(path: Path, data_dir: Path, text: str, lang: str) -> tuple[bool, str]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(text, encoding="utf-8")

    ok, messages = _validate_draft(path, data_dir, text, lang)
    if not ok:
        temp_path.unlink(missing_ok=True)
        return False, "\n".join(messages)

    backup_path = path.with_name(f"{path.name}.bak-{timestamp}")
    shutil.copy2(path, backup_path)
    temp_path.replace(path)
    return True, str(backup_path)


def render(data_dir: Path, lang: str) -> None:
    st.header(t("ui.data_editor.header", lang))

    roots = _allowed_roots(data_dir)
    files = _list_yaml_files(roots)
    if not files:
        st.info(t("ui.data_editor.empty_selection", lang))
        return

    file_options = [str(path) for path in files]
    selected = st.selectbox(t("ui.data_editor.file_select", lang), options=file_options)
    if not selected:
        st.info(t("ui.data_editor.empty_selection", lang))
        return

    path = Path(selected)
    if not _is_allowed(path, roots):
        st.error(t("ui.data_editor.disallowed_path", lang))
        return

    state_key = f"data_editor_text::{path}"
    if state_key not in st.session_state:
        st.session_state[state_key] = _read_text(path)
    text = st.session_state[state_key]

    last_modified = datetime.fromtimestamp(path.stat().st_mtime)
    st.write(f"{t('ui.data_editor.file_path', lang)}: {path}")
    st.write(
        f"{t('ui.data_editor.last_modified', lang)}: "
        f"{format_date(last_modified.date(), lang)} {last_modified.strftime('%H:%M:%S')}"
    )

    try:
        parsed = _parse_yaml(text)
        st.write(f"**{t('ui.data_editor.summary', lang)}**")
        st.json(_summarize(parsed))
    except Exception:
        st.warning(t("ui.data_editor.parse_failed", lang))

    updated_text = st.text_area(
        t("ui.data_editor.editor_label", lang),
        value=text,
        height=400,
    )
    st.session_state[state_key] = updated_text

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button(t("ui.data_editor.validate_draft", lang)):
            ok, messages = _validate_draft(path, data_dir, updated_text, lang)
            if ok:
                st.success(t("ui.data_editor.validation_ok", lang))
            else:
                st.error(t("ui.data_editor.validation_failed", lang))
                st.write(messages)
    with col2:
        if st.button(t("ui.data_editor.show_diff", lang)):
            original = _read_text(path).splitlines()
            current = updated_text.splitlines()
            diff = list(
                difflib.unified_diff(
                    original, current, fromfile=str(path), tofile=str(path)
                )
            )
            st.write(f"**{t('ui.data_editor.diff_header', lang)}**")
            if diff:
                st.code("\n".join(diff))
            else:
                st.info(t("ui.data_editor.diff_empty", lang))
    with col3:
        if st.button(t("ui.data_editor.normalize", lang)):
            try:
                normalized = normalize_data(_parse_yaml(updated_text))
                st.session_state[state_key] = dump_yaml(normalized)
                st.success(t("ui.data_editor.saved", lang))
            except Exception:
                st.error(t("ui.data_editor.parse_failed", lang))
    with col4:
        if st.button(t("ui.data_editor.revert", lang)):
            st.session_state[state_key] = _read_text(path)
            st.info(t("ui.data_editor.saved", lang))

    if st.button(t("ui.data_editor.save", lang)):
        ok, result = _safe_write(path, data_dir, st.session_state[state_key], lang)
        if ok:
            st.success(t("ui.data_editor.saved", lang))
            st.info(t("ui.data_editor.backup_saved", lang, path=result))
        else:
            st.error(t("ui.data_editor.save_failed", lang))
            st.write(result)

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import streamlit as st

from money_map.core.load import load_app_data


def _file_signature(path: Path) -> tuple[int, int]:
    if not path.exists():
        return (0, 0)
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def _collect_paths(data_dir: Path, workspace: Path | None) -> list[Path]:
    paths: list[Path] = []
    if data_dir.exists():
        paths.extend(sorted(data_dir.glob("*.yaml")))
        rulepacks_dir = data_dir / "rulepacks"
        if rulepacks_dir.exists():
            paths.extend(sorted(rulepacks_dir.glob("*.yaml")))
        knowledge_dir = data_dir / "knowledge"
        if knowledge_dir.exists():
            paths.extend(sorted(knowledge_dir.glob("*.yaml")))
    if workspace is not None:
        overlay = workspace / "overlay"
        if overlay.exists():
            paths.extend(sorted(overlay.glob("*.yaml")))
            overlay_rulepacks = overlay / "rulepacks"
            if overlay_rulepacks.exists():
                paths.extend(sorted(overlay_rulepacks.glob("*.yaml")))
    return paths


def _signature_tuple(paths: Iterable[Path]) -> tuple[tuple[str, int, int], ...]:
    return tuple(
        (str(path.resolve()), *_file_signature(path))
        for path in sorted(paths, key=lambda item: str(item.resolve()))
    )


@st.cache_data(show_spinner=False)
def load_app_data_cached(
    data_dir: str, country_code: str, workspace: str | None, signature: tuple
):
    _ = signature
    workspace_path = Path(workspace) if workspace else None
    return load_app_data(Path(data_dir), country_code=country_code, workspace=workspace_path)


def appdata_signature(data_dir: Path, workspace: Path | None) -> tuple[tuple[str, int, int], ...]:
    return _signature_tuple(_collect_paths(data_dir, workspace))

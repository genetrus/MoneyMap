from __future__ import annotations

import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import Any

from money_map.core.model import BaseModel, Field
from money_map.core.load import load_yaml
from money_map.core.yaml_utils import dump_yaml
from money_map.core.workspace import ensure_within_workspace, get_workspace_paths


class EvidenceItem(BaseModel):
    evidence_id: str
    title_key: str | None = None
    title: str | None = None
    type: str = "file"
    path: str | None = None
    note: str | None = None
    tags: list[str] = Field(default_factory=list)
    added_at: date | str = Field(default_factory=date.today)
    checksum_sha256: str | None = None
    related_entities: list[str] = Field(default_factory=list)


class EvidenceRegistry(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)


def load_registry(path: Path) -> EvidenceRegistry:
    if not path.exists():
        return EvidenceRegistry(items=[])
    data = load_yaml(path) or {}
    items = [EvidenceItem.model_validate(item) for item in data.get("items", []) or []]
    return EvidenceRegistry(items=items)


def save_registry(path: Path, registry: EvidenceRegistry) -> None:
    payload = {
        "items": [
            item.model_dump() if hasattr(item, "model_dump") else item.__dict__
            for item in sorted(registry.items, key=lambda item: item.evidence_id)
        ]
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(payload), encoding="utf-8")


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _relative_file_path(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    return relative.as_posix()


def add_file_evidence(
    workspace: Path,
    source_path: Path,
    evidence_id: str,
    title: str | None = None,
    tags: list[str] | None = None,
    related_entities: list[str] | None = None,
    force: bool = False,
) -> EvidenceItem:
    paths = get_workspace_paths(workspace)
    registry_path = paths.evidence / "registry.yaml"
    registry = load_registry(registry_path)

    if any(item.evidence_id == evidence_id for item in registry.items):
        raise ValueError("Evidence ID already exists")

    dest = paths.evidence_files / source_path.name
    ensure_within_workspace(paths.root, dest)
    if dest.exists() and not force:
        raise FileExistsError("Evidence file already exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(source_path.read_bytes())

    checksum = compute_sha256(dest)
    item = EvidenceItem(
        evidence_id=evidence_id,
        title=title,
        type="file",
        path=_relative_file_path(paths.evidence_files, dest),
        tags=tags or [],
        related_entities=related_entities or [],
        added_at=date.today().isoformat(),
        checksum_sha256=checksum,
    )
    registry.items.append(item)
    save_registry(registry_path, registry)
    return item


def add_note_evidence(
    workspace: Path,
    evidence_id: str,
    note: str,
    title: str | None = None,
    tags: list[str] | None = None,
    related_entities: list[str] | None = None,
) -> EvidenceItem:
    paths = get_workspace_paths(workspace)
    registry_path = paths.evidence / "registry.yaml"
    registry = load_registry(registry_path)

    if any(item.evidence_id == evidence_id for item in registry.items):
        raise ValueError("Evidence ID already exists")

    item = EvidenceItem(
        evidence_id=evidence_id,
        title=title,
        type="note",
        note=note,
        tags=tags or [],
        related_entities=related_entities or [],
        added_at=date.today().isoformat(),
    )
    registry.items.append(item)
    save_registry(registry_path, registry)
    return item


def validate_registry(workspace: Path) -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    paths = get_workspace_paths(workspace)
    registry_path = paths.evidence / "registry.yaml"
    if not registry_path.exists():
        return [], [("evidence.registry_missing", {})]
    registry = load_registry(registry_path)
    fatals: list[tuple[str, dict]] = []
    warns: list[tuple[str, dict]] = []
    ids: set[str] = set()
    for item in registry.items:
        if item.evidence_id in ids:
            fatals.append(("evidence.duplicate_id", {"evidence_id": item.evidence_id}))
        ids.add(item.evidence_id)
        if item.type == "file":
            if not item.path:
                fatals.append(("evidence.file_missing_path", {"evidence_id": item.evidence_id}))
                continue
            rel = Path(item.path)
            if rel.is_absolute() or ".." in rel.parts:
                fatals.append(("evidence.invalid_path", {"evidence_id": item.evidence_id}))
                continue
            file_path = paths.evidence_files / rel
            try:
                ensure_within_workspace(paths.root, file_path)
            except ValueError:
                fatals.append(("evidence.invalid_path", {"evidence_id": item.evidence_id}))
                continue
            if not file_path.exists():
                fatals.append(("evidence.file_missing", {"evidence_id": item.evidence_id}))
                continue
            checksum = compute_sha256(file_path)
            if item.checksum_sha256 and checksum != item.checksum_sha256:
                fatals.append(
                    (
                        "evidence.checksum_mismatch",
                        {"evidence_id": item.evidence_id},
                    )
                )
        if not item.related_entities:
            warns.append(("evidence.missing_relations", {"evidence_id": item.evidence_id}))
    if not registry.items:
        warns.append(("evidence.empty_registry", {}))
    return fatals, warns


def parse_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None

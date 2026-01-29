from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from money_map.core.model import BaseModel, Field
from money_map.core.yaml_utils import dump_yaml
from money_map.core.load import load_yaml

VALID_STATUSES = {"unverified", "verified", "needs_update", "deprecated"}


class ReviewEntry(BaseModel):
    entity_ref: str
    status: str = "unverified"
    verified_at: date | None = None
    reviewer: str | None = None
    notes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class ReviewsIndex(BaseModel):
    reviewed_at: date | str
    entries: list[ReviewEntry] = Field(default_factory=list)


def _to_date(value: date | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def load_reviews(path: Path) -> ReviewsIndex:
    if not path.exists():
        return ReviewsIndex(reviewed_at=date.today().isoformat(), entries=[])
    data = load_yaml(path) or {}
    entries = [ReviewEntry.model_validate(item) for item in data.get("entries", []) or []]
    reviewed_at = data.get("reviewed_at") or date.today().isoformat()
    return ReviewsIndex(reviewed_at=reviewed_at, entries=entries)


def save_reviews(path: Path, reviews: ReviewsIndex) -> None:
    payload = {
        "reviewed_at": reviews.reviewed_at,
        "entries": [
            entry.model_dump() if hasattr(entry, "model_dump") else entry.__dict__
            for entry in sorted(reviews.entries, key=lambda item: item.entity_ref)
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(payload), encoding="utf-8")


def find_review(reviews: ReviewsIndex, entity_ref: str) -> ReviewEntry | None:
    for entry in reviews.entries:
        if entry.entity_ref == entity_ref:
            return entry
    return None


def upsert_review(reviews: ReviewsIndex, entry: ReviewEntry) -> None:
    existing = find_review(reviews, entry.entity_ref)
    if existing is None:
        reviews.entries.append(entry)
    else:
        existing.status = entry.status
        existing.verified_at = entry.verified_at
        existing.reviewer = entry.reviewer
        existing.notes = entry.notes
        existing.evidence_refs = entry.evidence_refs


def review_status_for_entity(reviews: ReviewsIndex | None, entity_ref: str) -> ReviewEntry | None:
    if reviews is None:
        return None
    return find_review(reviews, entity_ref)


def normalize_review_date(value: str | date | None) -> date | None:
    return _to_date(value)


def validate_reviews_data(data: Any) -> list[tuple[str, dict]]:
    errors: list[tuple[str, dict]] = []
    if not isinstance(data, dict):
        return [("review.invalid_format", {})]
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        return [("review.invalid_entries", {})]
    ids = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append(("review.invalid_entry", {}))
            continue
        entity_ref = entry.get("entity_ref")
        if not entity_ref:
            errors.append(("review.missing_entity_ref", {}))
            continue
        if entity_ref in ids:
            errors.append(("review.duplicate_entity_ref", {"entity_ref": entity_ref}))
        ids.add(entity_ref)
        status = entry.get("status", "unverified")
        if status not in VALID_STATUSES:
            errors.append(("review.invalid_status", {"status": status}))
    return errors

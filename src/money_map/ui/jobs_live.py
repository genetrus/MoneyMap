"""Helpers for Jobs (Live) UI section with offline fallbacks."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from money_map.storage.fs import read_yaml

JOBS_ENDPOINT = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
JOBS_API_KEY = "jobboerse-jobsuche"
JOBS_SNAPSHOT_DIR = Path("data/snapshots/jobs_de")
OCCUPATION_MAP_PATH = Path("data/packs/de_muc/occupation_map.yaml")


def _pick(obj: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = obj.get(key)
        if value not in (None, ""):
            return value
    return None


def normalize_job(job: dict[str, Any]) -> dict[str, Any]:
    location = _pick(job, "arbeitsort", "arbeitsOrt", "ort", "location")
    city = ""
    if isinstance(location, dict):
        city = str(_pick(location, "ort", "stadt", "city") or "")
    elif isinstance(location, str):
        city = location

    return {
        "hashId": str(_pick(job, "hashId", "hashid") or ""),
        "refnr": str(_pick(job, "refnr", "referenznummer") or ""),
        "title": str(_pick(job, "titel", "beruf", "title") or ""),
        "company": str(_pick(job, "arbeitgeber", "arbeitgeberName", "firma", "company") or ""),
        "city": city,
        "publishedAt": str(
            _pick(job, "aktuelleVeroeffentlichungsdatum", "eintrittsdatum", "publishedAt") or ""
        ),
        "url": str(_pick(job, "externeUrl", "jobcenterUrl", "url") or ""),
        "raw": job,
    }


def _extract_jobs(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("stellenangebote", "jobs", "items", "results"):
            items = payload.get(key)
            if isinstance(items, list):
                return [x for x in items if isinstance(x, dict)]
    return []


def fetch_live_jobs(*, city: str, radius_km: int, days: int, size: int, profile: str) -> list[dict[str, Any]]:
    params = {
        "was": profile,
        "wo": city,
        "umkreis": radius_km,
        "size": size,
        "veroeffentlichtseit": days,
        "page": 1,
    }
    request = Request(f"{JOBS_ENDPOINT}?{urlencode(params)}", headers={"X-API-Key": JOBS_API_KEY})
    with urlopen(request, timeout=8.0) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [normalize_job(item) for item in _extract_jobs(payload)]


def latest_snapshot() -> tuple[list[dict[str, Any]], str | None]:
    files = sorted(JOBS_SNAPSHOT_DIR.glob("*.jsonl"))
    if not files:
        return [], None
    latest = files[-1]
    rows: list[dict[str, Any]] = []
    for line in latest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        rows.append(normalize_job(item if isinstance(item, dict) else {}))
    return rows, latest.name


def seed_slice(size: int) -> list[dict[str, Any]]:
    variants = read_yaml("data/variants.yaml").get("variants", [])
    compact = []
    for idx, variant in enumerate(variants[: max(1, min(size, 5))], start=1):
        compact.append(
            {
                "hashId": f"seed-{idx}",
                "refnr": f"seed-ref-{idx}",
                "title": str(variant.get("title", "")),
                "company": "Seed sample",
                "city": "Munich",
                "publishedAt": "",
                "url": "",
                "raw": {"seed_variant_id": variant.get("variant_id", "")},
            }
        )
    return compact


def resolve_jobs_source(*, city: str, radius_km: int, days: int, size: int, profile: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    try:
        live_rows = fetch_live_jobs(
            city=city,
            radius_km=radius_km,
            days=days,
            size=size,
            profile=profile,
        )
        if live_rows:
            return live_rows, {"source": "live", "snapshot": "", "fetched_at": datetime.now(timezone.utc).isoformat()}
    except Exception:
        pass

    snapshot_rows, snapshot_name = latest_snapshot()
    if snapshot_rows:
        return snapshot_rows[:size], {
            "source": "cache",
            "snapshot": snapshot_name or "",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    return seed_slice(size), {
        "source": "seed",
        "snapshot": "",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _contains_any(value: str, needles: list[str]) -> bool:
    v = value.lower()
    return any(n.lower() in v for n in needles)


def map_job_to_occupation(job: dict[str, Any]) -> dict[str, Any]:
    occupation_map = read_yaml(OCCUPATION_MAP_PATH)
    maps = sorted(occupation_map.get("maps", []), key=lambda x: int(x.get("priority", 0)), reverse=True)

    title = str(job.get("title", ""))
    for item in maps:
        if not item.get("active", True):
            continue
        match = item.get("match", {})
        if match.get("always") is True:
            assign = item.get("assign", {})
            return {"map_id": item.get("id", ""), "assign": assign}
        if _contains_any(title, list(match.get("beruf_any", []))):
            assign = item.get("assign", {})
            return {"map_id": item.get("id", ""), "assign": assign}

    return {"map_id": "", "assign": {"cell_id": "A1", "taxonomy_id": "service_fee", "tags": ["needs_manual_review"]}}


def create_variant_draft(job: dict[str, Any]) -> dict[str, Any]:
    mapped = map_job_to_occupation(job)
    title = str(job.get("title", "Untitled vacancy")).strip() or "Untitled vacancy"
    draft_id = f"draft.{(job.get('hashId') or job.get('refnr') or 'job').strip() or 'job'}"
    return {
        "variant_id": draft_id,
        "title": f"{title} (Draft)",
        "summary": f"Drafted from vacancy in {job.get('city', '')}.",
        "tags": list(mapped["assign"].get("tags", [])),
        "cell_id": mapped["assign"].get("cell_id", "A1"),
        "taxonomy_id": mapped["assign"].get("taxonomy_id", "service_fee"),
        "source": {
            "type": "job_vacancy",
            "hashId": job.get("hashId", ""),
            "refnr": job.get("refnr", ""),
            "title": title,
            "map_id": mapped.get("map_id", ""),
        },
    }

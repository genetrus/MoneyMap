#!/usr/bin/env python3
"""Ingest Germany Jobsuche snapshot data into JSONL files."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_ENDPOINT = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
DEFAULT_API_KEY = "jobboerse-jobsuche"
SNAPSHOT_DIR = Path("data/snapshots/jobs_de")


def _pick(obj: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return None


def _normalize_job(job: dict[str, Any], endpoint: str) -> dict[str, Any]:
    location = _pick(job, "arbeitsort", "arbeitsOrt", "ort", "location")
    if isinstance(location, dict):
        city = _pick(location, "ort", "stadt", "city")
        region = _pick(location, "region", "bundesland", "state")
    else:
        city = location
        region = None

    employer = _pick(job, "arbeitgeber", "arbeitgeberName", "firma", "company")
    if isinstance(employer, dict):
        employer_name = _pick(employer, "name", "firma", "company")
    else:
        employer_name = employer

    salary = _pick(job, "gehalt", "salary")
    salary_min = salary_max = salary_currency = None
    if isinstance(salary, dict):
        salary_min = _pick(salary, "von", "min", "minimum")
        salary_max = _pick(salary, "bis", "max", "maximum")
        salary_currency = _pick(salary, "waehrung", "currency")

    normalized = {
        "hashId": _pick(job, "hashId", "hashid"),
        "refnr": _pick(job, "refnr", "referenznummer"),
        "title": _pick(job, "titel", "beruf", "title"),
        "company": employer_name,
        "city": city,
        "region": region,
        "employmentType": _pick(job, "arbeitszeitmodell", "arbeitszeit", "employmentType"),
        "publishedAt": _pick(
            job, "aktuelleVeroeffentlichungsdatum", "eintrittsdatum", "publishedAt"
        ),
        "updatedAt": _pick(job, "modifikationsTimestamp", "updatedAt"),
        "url": _pick(job, "externeUrl", "jobcenterUrl", "url"),
        "salaryMin": salary_min,
        "salaryMax": salary_max,
        "salaryCurrency": salary_currency,
        "source": "jobsuche",
        "sourceEndpoint": endpoint,
        "raw": job,
    }
    return normalized


def _dedupe_key(job: dict[str, Any]) -> str | None:
    key = job.get("hashId") or job.get("refnr")
    if key is None:
        return None
    return str(key)


def _dedupe_jobs(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    no_key_jobs: list[dict[str, Any]] = []
    for job in jobs:
        key = _dedupe_key(job)
        if key is None:
            no_key_jobs.append(job)
            continue
        unique[key] = job
    return [*unique.values(), *no_key_jobs]


def _request_jobs(endpoint: str, params: dict[str, Any], timeout_s: float) -> list[dict[str, Any]]:
    query = urlencode(params)
    url = f"{endpoint}?{query}"
    request = Request(url, headers={"X-API-Key": DEFAULT_API_KEY})
    with urlopen(request, timeout=timeout_s) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("stellenangebote", "jobs", "items", "results"):
            items = payload.get(key)
            if isinstance(items, list):
                return items
    raise ValueError("Unexpected Jobsuche response format: expected list or dict with jobs array")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    if not path.exists():
        return jobs
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            jobs.append(json.loads(line))
    return jobs


def _write_jsonl(path: Path, jobs: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for job in jobs:
            fh.write(json.dumps(job, ensure_ascii=False) + "\n")


def _find_latest_snapshot_for_day(day: dt.date) -> Path | None:
    pattern = f"{day.isoformat()}_*.jsonl"
    files = sorted(SNAPSHOT_DIR.glob(pattern))
    if not files:
        return None
    return files[-1]


def _build_target_path(mode: str, now: dt.datetime) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if mode == "update":
        existing = _find_latest_snapshot_for_day(now.date())
        if existing is not None:
            return existing
    name = f"{now.date().isoformat()}_{now.strftime('%H%M%S')}.jsonl"
    return SNAPSHOT_DIR / name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ingest jobs from Jobsuche API and store normalized JSONL snapshots "
            "in data/snapshots/jobs_de/."
        )
    )
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Jobsuche endpoint URL")
    parser.add_argument("--was", default="", help="Search term (what)")
    parser.add_argument("--wo", default="", help="Search location")
    parser.add_argument("--umkreis", type=int, default=25, help="Search radius in km")
    parser.add_argument("--size", type=int, default=50, help="Page size")
    parser.add_argument(
        "--veroeffentlichtseit",
        type=int,
        default=7,
        help="Days since publication",
    )
    parser.add_argument("--page", type=int, default=1, help="Page number")
    parser.add_argument(
        "--mode",
        choices=("append", "update"),
        default="append",
        help="append=create new snapshot, update=merge into latest snapshot of the day",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    params = {
        "was": args.was,
        "wo": args.wo,
        "umkreis": args.umkreis,
        "size": args.size,
        "veroeffentlichtseit": args.veroeffentlichtseit,
        "page": args.page,
    }

    raw_jobs = _request_jobs(args.endpoint, params=params, timeout_s=args.timeout)
    normalized_jobs = [_normalize_job(job, endpoint=args.endpoint) for job in raw_jobs]
    incoming = _dedupe_jobs(normalized_jobs)

    now = dt.datetime.now(dt.timezone.utc)
    target_path = _build_target_path(mode=args.mode, now=now)

    if args.mode == "update" and target_path.exists():
        existing = _read_jsonl(target_path)
        merged = _dedupe_jobs([*existing, *incoming])
        _write_jsonl(target_path, merged)
        print(
            f"Updated {target_path}: existing={len(existing)}, incoming={len(incoming)}, total={len(merged)}"
        )
        return

    _write_jsonl(target_path, incoming)
    print(f"Written {target_path}: total={len(incoming)}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

from money_map.ui.jobs_live import create_variant_draft, map_job_to_occupation, resolve_jobs_source


def test_map_job_to_occupation_matches_known_role() -> None:
    mapped = map_job_to_occupation({"title": "Senior Software Engineer"})
    assert mapped["assign"]["cell_id"] == "A2"
    assert mapped["assign"]["taxonomy_id"] == "service_fee"


def test_create_variant_draft_uses_occupation_map() -> None:
    draft = create_variant_draft(
        {
            "hashId": "abc123",
            "refnr": "ref1",
            "title": "Courier Driver",
            "city": "Munich",
        }
    )
    assert draft["variant_id"] == "draft.abc123"
    assert draft["source"]["type"] == "job_vacancy"
    assert draft["cell_id"] in {"A1", "A2", "B1", "B2"}


def test_resolve_jobs_source_falls_back_without_snapshot(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("money_map.ui.jobs_live.JOBS_SNAPSHOT_DIR", tmp_path / "missing")

    def _boom(**_kwargs):
        raise OSError("network disabled")

    monkeypatch.setattr("money_map.ui.jobs_live.fetch_live_jobs", _boom)
    rows, meta = resolve_jobs_source(city="Munich", radius_km=10, days=3, size=2, profile="qa")
    assert meta["source"] == "seed"
    assert len(rows) >= 1

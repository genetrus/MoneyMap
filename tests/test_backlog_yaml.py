from __future__ import annotations

from pathlib import Path

import yaml


def test_backlog_yaml_schema():
    backlog_path = Path(__file__).resolve().parents[1] / "docs" / "backlog.yaml"
    data = yaml.safe_load(backlog_path.read_text(encoding="utf-8"))

    assert data["version"] == 1
    assert "epics" in data

    priority_scheme = data["priority_scheme"]
    allowed_priorities = set(priority_scheme.keys())
    allowed_statuses = set(data["status_scheme"])

    epic_ids = set()
    story_ids = set()
    task_ids = set()

    for epic in data["epics"]:
        epic_id = epic["epic_id"]
        assert epic_id not in epic_ids
        epic_ids.add(epic_id)
        assert epic["priority"] in allowed_priorities
        assert epic["status"] in allowed_statuses
        _assert_spec_refs(epic["spec_refs"])

        for story in epic.get("stories", []):
            story_id = story["story_id"]
            assert story_id not in story_ids
            story_ids.add(story_id)
            assert story["priority"] in allowed_priorities
            assert story["status"] in allowed_statuses
            _assert_spec_refs(story["spec_refs"])

            for task in story.get("tasks", []):
                task_id = task["task_id"]
                assert task_id not in task_ids
                task_ids.add(task_id)
                assert task["priority"] in allowed_priorities
                assert task["status"] in allowed_statuses
                _assert_spec_refs(task["spec_refs"])


def _assert_spec_refs(spec_refs: list[dict[str, str]]) -> None:
    assert isinstance(spec_refs, list)
    assert spec_refs, "spec_refs must not be empty"
    for ref in spec_refs:
        assert "pdf" in ref
        assert "pages" in ref
        assert ref["pdf"], "pdf filename is required"
        assert ref["pages"], "pages entry is required"

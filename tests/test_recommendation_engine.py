import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from money_map.app.cli import export_command
from money_map.core.load import load_app_data
from money_map.core.model import UserProfile
from money_map.core.plan import build_plan
from money_map.core.recommend import recommend


class TestRecommendationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.appdata = load_app_data(Path("data"))
        self.profile = UserProfile.model_validate(
            json.loads(Path("profiles/demo_fast_start.yaml").read_text(encoding="utf-8"))
        )

    def test_recommendation_deterministic(self) -> None:
        first = recommend(self.profile, self.appdata, top_n=5)
        second = recommend(self.profile, self.appdata, top_n=5)
        first_ids = [item.variant_id for item in first.ranked_variants]
        second_ids = [item.variant_id for item in second.ranked_variants]
        self.assertEqual(first_ids, second_ids)
        self.assertTrue(first.ranked_variants[0].pros)
        self.assertTrue(first.ranked_variants[0].cons)

    def test_regulated_stale_blocker(self) -> None:
        appdata = deepcopy(self.appdata)
        regulated_variant = appdata.variants[0]
        regulated_variant.tags.append("regulated")
        regulated_variant.review_date = "2020-01-01"
        result = recommend(self.profile, appdata, top_n=6)
        target = next(
            item
            for item in result.ranked_variants
            if item.variant_id == regulated_variant.variant_id
        )
        self.assertIn("reason.legal.force_check", target.blockers)

    def test_plan_output(self) -> None:
        plan = build_plan("v002", self.profile, self.appdata)
        self.assertEqual(4, len(plan.week_plan))
        self.assertEqual(4, len(plan.steps))
        self.assertTrue(plan.compliance_checklist)
        artifact_names = {artifact["filename"] for artifact in plan.artifacts}
        self.assertIn("checklist.md", artifact_names)

    def test_export_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "exports"
            export_command(Path("profiles/demo_fast_start.yaml"), out_path, Path("data"), "en")
            first_snapshot = {
                path.name: path.read_text(encoding="utf-8")
                for path in out_path.iterdir()
                if path.is_file()
            }
            export_command(Path("profiles/demo_fast_start.yaml"), out_path, Path("data"), "en")
            second_snapshot = {
                path.name: path.read_text(encoding="utf-8")
                for path in out_path.iterdir()
                if path.is_file()
            }
            self.assertEqual(first_snapshot, second_snapshot)
            self.assertTrue(
                {"plan.md", "result.json", "profile.yaml", "checklist.md"}.issubset(
                    first_snapshot
                )
            )

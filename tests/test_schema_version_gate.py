import json
import shutil
import tempfile
import unittest
from pathlib import Path

from money_map.core.validate import validate_app_data


class TestSchemaVersionGate(unittest.TestCase):
    def test_schema_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "data"
            shutil.copytree(Path("data"), temp_path)
            meta_path = temp_path / "meta.yaml"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["schema_version"] = "0.0.0"
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            fatals, _ = validate_app_data(temp_path, strict=True)
            keys = {fatal[0] for fatal in fatals}
            self.assertIn("validate.schema_version_mismatch", keys)

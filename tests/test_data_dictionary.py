import tempfile
import unittest
from pathlib import Path

from money_map.core.data_dictionary import generate_data_dictionary


class TestDataDictionary(unittest.TestCase):
    def test_generate_data_dictionary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "data_dictionary.md"
            generate_data_dictionary(Path("data"), out_path)
            content = out_path.read_text(encoding="utf-8")
            self.assertTrue(content.strip())

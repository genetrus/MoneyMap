from datetime import date
from pathlib import Path

from money_map.core.load import load_app_data, load_yaml
from money_map.core.model import UserProfile
from money_map.core.simulate import simulation_to_json_text, simulate_variant


def test_simulation_snapshot() -> None:
    data_dir = Path("data")
    appdata = load_app_data(data_dir)
    profile_data = load_yaml(Path("profiles/demo_fast_start.yaml"))
    profile = UserProfile.model_validate(profile_data)
    variant = next(item for item in appdata.variants if item.variant_id == "v001")
    result = simulate_variant(profile, variant, appdata.presets[0], 6, date(2026, 1, 1))
    snapshot = Path("tests/snapshots/simulation.json")
    assert simulation_to_json_text(result) == snapshot.read_text(encoding="utf-8")

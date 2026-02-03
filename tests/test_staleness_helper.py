from dataclasses import replace

from money_map.core.load import load_app_data
from money_map.core.model import StalenessPolicy
from money_map.core.recommend import is_variant_stale


def test_is_variant_stale_helper_flags_old_review_date():
    app_data = load_app_data()
    base_variant = app_data.variants[0]
    stale_variant = replace(base_variant, review_date="2000-01-01")

    assert is_variant_stale(stale_variant, StalenessPolicy(stale_after_days=1))

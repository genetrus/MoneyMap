from money_map.app.api import recommend_variants


def test_recommend_deterministic():
    result_a = recommend_variants(
        profile_path="profiles/demo_fast_start.yaml",
        objective="fastest_money",
        top_n=3,
    )
    result_b = recommend_variants(
        profile_path="profiles/demo_fast_start.yaml",
        objective="fastest_money",
        top_n=3,
    )

    ids_a = [rec.variant.variant_id for rec in result_a.ranked_variants]
    ids_b = [rec.variant.variant_id for rec in result_b.ranked_variants]
    assert ids_a == ids_b

from money_map.core.classify import classify_idea_text
from money_map.core.load import load_app_data


def test_classify_is_deterministic_for_same_input() -> None:
    app_data = load_app_data("data")
    idea = "I want to do remote freelance writing for local businesses."

    first = classify_idea_text(idea, app_data=app_data, data_dir="data")
    second = classify_idea_text(idea, app_data=app_data, data_dir="data")

    assert first == second
    assert first.top3
    assert first.top3[0].taxonomy_id == "service_fee"


def test_classify_marks_ambiguous_when_top_scores_are_close() -> None:
    app_data = load_app_data("data")
    idea = "I can do local childcare and maybe take commission percent for referrals."

    result = classify_idea_text(idea, app_data=app_data, data_dir="data")

    assert result.ambiguity in {"clear", "ambiguous"}
    if len(result.top3) > 1:
        gap = result.top3[0].score - result.top3[1].score
        if gap < 1.0:
            assert result.ambiguity == "ambiguous"


def test_classify_uses_keywords_and_tag_mappings() -> None:
    app_data = load_app_data("data")
    idea = "subscription monthly recurring remote"

    result = classify_idea_text(idea, app_data=app_data, data_dir="data")

    assert result.top3[0].taxonomy_id == "subscription"
    assert result.suggested_tags["value_measure"] == "recurring"
    assert "subscription" in result.matched_keywords

from pathlib import Path


def test_graph_fallback_has_three_levels_contract() -> None:
    source = Path("src/money_map/ui/components.py").read_text(encoding="utf-8")
    assert "Interactive view unavailable, fallback applied." in source
    assert "st.graphviz_chart" in source
    assert "Graph fallback: list/table" in source
    assert "st.dataframe(nodes_rows" in source
    assert "st.dataframe(edges_rows" in source

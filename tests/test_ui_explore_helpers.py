from money_map.ui.data_status import variants_by_cell


def test_variants_by_cell_is_stable_sorted() -> None:
    class V:
        def __init__(self, cell: str):
            self.cell = cell

    variants = [V("B2"), V("A1"), V("A1")]
    rows = variants_by_cell(variants, cell_resolver=lambda v: v.cell)
    assert rows == [{"label": "A1", "count": 2}, {"label": "B2", "count": 1}]

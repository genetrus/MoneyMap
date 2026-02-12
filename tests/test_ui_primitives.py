import importlib.util

import pytest


@pytest.mark.skipif(
    importlib.util.find_spec("streamlit") is None,
    reason="streamlit not installed in test environment",
)
def test_action_contract_contains_required_keys() -> None:
    from money_map.ui.components import build_action_contract

    contract = build_action_contract(
        label="Recompute",
        intent="Обновить ранжирование",
        effect="Пересчитает результаты",
        next_step="Просмотри карточки",
        undo="Измени фильтры",
    )

    assert set(contract.keys()) == {"Label", "Intent", "Effect", "Next", "Undo"}
    assert contract["Label"] == "Recompute"


@pytest.mark.skipif(
    importlib.util.find_spec("streamlit") is None,
    reason="streamlit not installed in test environment",
)
def test_action_contract_help_renders_all_sections() -> None:
    from money_map.ui.components import action_contract_help, build_action_contract

    contract = build_action_contract(
        label="Select",
        intent="Выбрать вариант",
        effect="Сохранит selected_variant_id",
        next_step="Перейти в Plan",
        undo="Снять выбор",
    )

    text = action_contract_help(contract)
    assert "Label:" in text
    assert "Intent:" in text
    assert "Effect:" in text
    assert "Next:" in text
    assert "Undo:" in text

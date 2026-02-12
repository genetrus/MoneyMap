from pathlib import Path


def _read_ui_app() -> str:
    return Path("src/money_map/ui/app.py").read_text(encoding="utf-8")


def test_ui_cache_contracts_present() -> None:
    source = _read_ui_app()
    assert "@st.cache_resource\ndef _get_app_data" in source
    assert "@st.cache_data\ndef _get_validation" in source
    assert "@st.cache_data\ndef _get_recommendations" in source


def test_ui_recommendations_empty_state_contract_present() -> None:
    source = _read_ui_app()
    assert "render_empty_state(" in source
    assert "Quick fix: allow prep" in source
    assert "Quick fix: relax legal" in source
    assert "Quick fix: extend time" in source


def test_ui_export_artifact_panel_contract_present() -> None:
    source = _read_ui_app()
    assert "### Artifacts" in source
    assert "Preview plan.md" in source
    assert "Preview result.json" in source
    assert "Preview profile.yaml" in source
    assert "### Export metadata" in source
    assert "Copy run command" in source


def test_ui_plan_tabs_contract_present() -> None:
    source = _read_ui_app()
    assert "st.tabs(" in source
    assert "Checklist" in source
    assert "4 weeks" in source
    assert "Compliance" in source
    assert "Step detail drawer" in source


def test_ui_global_shell_guidance_contract_present() -> None:
    source = _read_ui_app()
    assert "guide_panel_layout" in source
    assert "render_guide_panel(runtime=guidance_runtime" in source
    components_source = Path("src/money_map/ui/components.py").read_text(encoding="utf-8")
    assert "context-open-data-status" in components_source
    assert "context-open-profile" in components_source
    assert "context-open-drawer" in components_source


def test_ui_data_status_profile_guidance_contract_present() -> None:
    source = _read_ui_app()
    assert "pages.data_status.goal_hint" in source
    assert "data-status-go-profile" in source
    assert "data-status-rerun-validate" in source
    assert "pages.profile.goal_hint" in source
    assert "profile-go-recommendations" in source
    assert "pages.profile.blocked_reason" in source

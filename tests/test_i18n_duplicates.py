from pathlib import Path

from money_map.i18n.audit import audit_i18n


def test_i18n_duplicate_detection() -> None:
    i18n_dir = Path("src/money_map/i18n")
    dup_file = i18n_dir / "en" / "dup_test.yaml"
    dup_file.parent.mkdir(parents=True, exist_ok=True)
    dup_file.write_text('app.title: "Duplicate"\n', encoding="utf-8")
    try:
        fatals, warns = audit_i18n(
            Path("data"),
            ["en"],
            report_duplicates=True,
            strict_core=True,
        )
        assert any(item.key == "app.title" for item in fatals + warns)
    finally:
        dup_file.unlink(missing_ok=True)

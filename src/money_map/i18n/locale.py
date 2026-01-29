from __future__ import annotations

from datetime import date, datetime
from typing import Any

try:
    from babel.dates import format_date as babel_format_date
    from babel.numbers import format_currency, format_decimal, format_percent as babel_format_percent
except ImportError:  # pragma: no cover - optional dependency
    babel_format_date = None
    format_decimal = None
    format_currency = None
    babel_format_percent = None

LANG_SETTINGS = {
    "en": {
        "thousand": ",",
        "decimal": ".",
        "date_order": "mdy",
        "date_sep": "/",
        "date_pattern": "MM/dd/yyyy",
        "currency_suffix": False,
    },
    "de": {
        "thousand": ".",
        "decimal": ",",
        "date_order": "dmy",
        "date_sep": ".",
        "date_pattern": "dd.MM.yyyy",
        "currency_suffix": True,
    },
    "fr": {
        "thousand": "\u202f",
        "decimal": ",",
        "date_order": "dmy",
        "date_sep": "/",
        "date_pattern": "dd/MM/yyyy",
        "currency_suffix": True,
    },
    "es": {
        "thousand": ".",
        "decimal": ",",
        "date_order": "dmy",
        "date_sep": "/",
        "date_pattern": "dd/MM/yyyy",
        "currency_suffix": True,
    },
    "pl": {
        "thousand": " ",
        "decimal": ",",
        "date_order": "dmy",
        "date_sep": ".",
        "date_pattern": "dd.MM.yyyy",
        "currency_suffix": True,
    },
    "ru": {
        "thousand": " ",
        "decimal": ",",
        "date_order": "dmy",
        "date_sep": ".",
        "date_pattern": "dd.MM.yyyy",
        "currency_suffix": True,
    },
}


def _settings(lang: str) -> dict[str, Any]:
    return LANG_SETTINGS.get(lang, LANG_SETTINGS["en"])


def _to_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return date.today()


def _group_digits(value: str, sep: str) -> str:
    if len(value) <= 3:
        return value
    groups = []
    while value:
        groups.append(value[-3:])
        value = value[:-3]
    return sep.join(reversed(groups))


def _format_number(value: float, decimals: int, lang: str) -> str:
    settings = _settings(lang)
    negative = value < 0
    formatted = f"{abs(value):.{decimals}f}"
    if decimals == 0:
        integer_part, decimal_part = formatted, ""
    else:
        integer_part, decimal_part = formatted.split(".")
    grouped = _group_digits(integer_part, settings["thousand"])
    if decimals > 0:
        result = f"{grouped}{settings['decimal']}{decimal_part}"
    else:
        result = grouped
    if negative:
        result = f"-{result}"
    return result


def format_date(dt: date | str, lang: str) -> str:
    value = _to_date(dt)
    settings = _settings(lang)
    sep = settings["date_sep"]
    if babel_format_date:
        return babel_format_date(value, format=settings["date_pattern"], locale=lang)
    if settings["date_order"] == "mdy":
        return f"{value.month:02d}{sep}{value.day:02d}{sep}{value.year:04d}"
    return f"{value.day:02d}{sep}{value.month:02d}{sep}{value.year:04d}"


def format_int(n: int, lang: str) -> str:
    if format_decimal:
        return format_decimal(n, locale=lang)
    return _format_number(float(n), 0, lang)


def format_money_eur(amount: float, lang: str) -> str:
    settings = _settings(lang)
    if format_currency:
        return format_currency(amount, "EUR", locale=lang)
    formatted = _format_number(amount, 2, lang)
    if settings["currency_suffix"]:
        return f"{formatted} €"
    return f"€{formatted}"


def format_percent(x: float, lang: str) -> str:
    value = float(x * 100 if x <= 1 else x)
    if babel_format_percent:
        return babel_format_percent(value / 100, locale=lang)
    decimals = 0 if value.is_integer() else 1
    formatted = _format_number(value, decimals, lang)
    return f"{formatted}%"

"""Error types for MoneyMap."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MoneyMapError(Exception):
    code: str
    message: str
    hint: str
    details: str | None = None
    run_id: str | None = None
    extra: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class DataValidationError(MoneyMapError):
    def __init__(
        self,
        message: str,
        hint: str,
        *,
        run_id: str | None = None,
        details: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="DATA_VALIDATION_ERROR",
            message=message,
            hint=hint,
            details=details,
            run_id=run_id,
            extra=extra,
        )


class RulepackStaleWarning(MoneyMapError):
    def __init__(
        self,
        message: str,
        hint: str,
        *,
        run_id: str | None = None,
        details: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="RULEPACK_STALE",
            message=message,
            hint=hint,
            details=details,
            run_id=run_id,
            extra=extra,
        )


class InternalError(MoneyMapError):
    def __init__(
        self,
        message: str = "Unexpected error",
        hint: str = "Check logs for details",
        *,
        run_id: str | None = None,
        details: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code="INTERNAL_ERROR",
            message=message,
            hint=hint,
            details=details,
            run_id=run_id,
            extra=extra,
        )

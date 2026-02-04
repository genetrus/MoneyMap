"""Run context and logging helpers for MoneyMap CLI."""

from __future__ import annotations

import contextvars
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

_RUN_CONTEXT: contextvars.ContextVar["RunContext | None"] = contextvars.ContextVar(
    "money_map_run_context",
    default=None,
)
_LOGGER_NAME = "money_map"


@dataclass(frozen=True)
class RunContext:
    run_id: str
    command: str
    data_dir: str
    out_dir: str
    log_path: Path
    started_at: str


def init_run_context(command: str, data_dir: str, out_dir: str = "exports") -> RunContext:
    run_id = str(uuid4())
    log_path = Path(out_dir) / "logs" / f"{run_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _configure_logger(log_path)
    started_at = datetime.now(timezone.utc).isoformat()
    context = RunContext(
        run_id=run_id,
        command=command,
        data_dir=data_dir,
        out_dir=out_dir,
        log_path=log_path,
        started_at=started_at,
    )
    _RUN_CONTEXT.set(context)
    log_event(
        "run_start",
        run_id=run_id,
        command=command,
        data_dir=data_dir,
        out_dir=out_dir,
        started_at=started_at,
    )
    return context


def get_run_context() -> RunContext | None:
    return _RUN_CONTEXT.get()


def log_event(event: str, **fields: object) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        return
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))


def log_exception(message: str, **fields: object) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        return
    payload = {"event": "exception", "message": message, **fields}
    logger.exception(json.dumps(payload, ensure_ascii=False, default=str))


def _configure_logger(log_path: Path) -> None:
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

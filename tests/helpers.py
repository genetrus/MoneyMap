from __future__ import annotations

import re
import socket


def block_network(monkeypatch) -> None:
    def _guard(*_args, **_kwargs):
        raise RuntimeError("Network access disabled in tests")

    monkeypatch.setattr(socket.socket, "connect", _guard, raising=True)
    monkeypatch.setattr(socket, "create_connection", _guard, raising=True)


def extract_section(plan_md: str, header: str) -> list[str]:
    lines = plan_md.splitlines()
    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == header:
            start_idx = idx + 1
            break
    if start_idx is None:
        return []
    section_lines = []
    for line in lines[start_idx:]:
        if line.startswith("## "):
            break
        section_lines.append(line)
    return section_lines


def count_numbered_lines(lines: list[str]) -> int:
    return sum(1 for line in lines if re.match(r"^\d+\.\s", line.strip()))


def count_checkbox_lines(lines: list[str]) -> int:
    return sum(1 for line in lines if line.strip().startswith("- [ ]"))


def count_bullet_lines(lines: list[str]) -> int:
    return sum(1 for line in lines if line.strip().startswith("- "))

from __future__ import annotations

import socket

import pytest

from money_map.app import cli


def test_disable_network_env_blocks_socket(monkeypatch) -> None:
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection
    monkeypatch.setenv("MONEY_MAP_DISABLE_NETWORK", "1")

    try:
        cli._disable_network_if_requested()
        with pytest.raises(RuntimeError, match="Network access disabled"):
            socket.create_connection(("example.com", 80))
        with pytest.raises(RuntimeError, match="Network access disabled"):
            socket.socket().connect_ex(("example.com", 80))
    finally:
        socket.socket.connect = original_connect
        socket.socket.connect_ex = original_connect_ex
        socket.create_connection = original_create_connection

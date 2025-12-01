import types
from pathlib import Path

import pytest

import src.app_context as mod


class FakeConnection:
    def __init__(self, connected=True):
        self.connected = connected
        self.closed = False

    def is_connected(self):
        return self.connected

    def close(self):
        self.closed = True


def test_create_app_context_success(monkeypatch):
    monkeypatch.setattr(mod.DockerFinder, "get_mysql_host_information", lambda self: (3306, "127.0.0.1"))

    fake_conn = FakeConnection()
    monkeypatch.setattr(mod.mysql.connector, "connect", lambda **kwargs: fake_conn)

    captured = {}

    class FakeHelper:
        def __init__(self, conn):
            captured["conn"] = conn

    monkeypatch.setattr(mod, "HelperFunct", FakeHelper)

    ctx = mod.create_app_context()

    assert ctx.conn is fake_conn
    assert captured["conn"] is fake_conn
    assert ctx.store.__class__ is FakeHelper
    assert ctx.default_save_dir.name == "project_insights"
    assert ctx.default_save_dir.parent.name == "User_config_files"


def test_create_app_context_failure_after_retries(monkeypatch):
    monkeypatch.setattr(mod.DockerFinder, "get_mysql_host_information", lambda self: (3306, "127.0.0.1"))

    def fail_connect(**kwargs):
        raise mod.Error("not ready")

    monkeypatch.setattr(mod.mysql.connector, "connect", fail_connect)

    with pytest.raises(Exception):
        mod.create_app_context()


def test_app_context_close_swallows_errors(monkeypatch):
    conn = FakeConnection()
    ctx = mod.AppContext(
        conn=conn,
        store=types.SimpleNamespace(),
        legacy_save_dir=Path("/tmp/legacy"),
        default_save_dir=Path("/tmp/default"),
    )
    ctx.close()
    assert conn.closed is True

import types
from pathlib import Path

import pytest

# Covers DB context initialization and cleanup helpers.
import src.core.app_context as mod


class FakeConnection:
    def __init__(self, connected=True):
        self.connected = connected
        self.closed = False

    def is_connected(self):
        return self.connected

    def close(self):
        self.closed = True


def test_create_app_context_success(monkeypatch):
    """Check that a successful DB connection builds the context.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate context initialization.
    """
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
    """Check that repeated DB failures raise an error.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate error handling.
    """
    monkeypatch.setattr(mod.DockerFinder, "get_mysql_host_information", lambda self: (3306, "127.0.0.1"))

    def fail_connect(**kwargs):
        raise mod.Error("not ready")

    monkeypatch.setattr(mod.mysql.connector, "connect", fail_connect)

    with pytest.raises(Exception):
        mod.create_app_context()


def test_app_context_close_swallows_errors(monkeypatch):
    """Check that closing the context does not raise errors.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate safe cleanup.
    """
    conn = FakeConnection()
    ctx = mod.AppContext(
        conn=conn,
        store=types.SimpleNamespace(),
        legacy_save_dir=Path("/tmp/legacy"),
        default_save_dir=Path("/tmp/default"),
        external_consent=False
    )
    ctx.close()
    assert conn.closed is True

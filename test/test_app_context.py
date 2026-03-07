import types
import os
from pathlib import Path

import pytest

# Prevent module-level runtimeAppContext creation from requiring a live DB during test import.
os.environ.setdefault("SKIP_DB_INIT", "1")

# Covers DB context initialization and cleanup helpers.
import src.core.app_context as mod


class FakeConnection:
    def __init__(self):
        self.closed = False

    def execute(self, *args, **kwargs):
        pass

    def close(self):
        self.closed = True


def test_create_app_context_success(monkeypatch):
    """Check that a successful DB connection builds the context.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate context initialization.
    """
    # Force DB init path for this test even if the suite sets SKIP_DB_INIT=1.
    monkeypatch.setenv("SKIP_DB_INIT", "0")


    fake_conn = FakeConnection()
    monkeypatch.setattr(mod.sqlite3, "connect", lambda *args, **kwargs: fake_conn)

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
    assert ctx.external_consent == False
    assert ctx.currently_uploaded_file == None


def test_create_app_context_failure_after_retries(monkeypatch):
    """Check that repeated DB failures raise an error.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate error handling.
    """
    # Force DB init path for this test even if the suite sets SKIP_DB_INIT=1.
    monkeypatch.setenv("SKIP_DB_INIT", "0")

    def fail_connect(*args, **kwargs):
        raise Exception("cannot open database")

    monkeypatch.setattr(mod.sqlite3, "connect", fail_connect)

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
        external_consent=False,
        data_consent=False,
        currently_uploaded_file=None
    )
    ctx.close()
    assert conn.closed is True

import pytest
from types import SimpleNamespace

# Tests for the CLI entrypoint orchestration and consent flow.
import src.main as main_mod


class DummyContext:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_run_exits_when_consent_declined(monkeypatch):
    consent = SimpleNamespace(has_external_consent=False, has_data_consent=False)
    consent.ask_for_consent = lambda: False
    monkeypatch.setattr(main_mod, "UserConsent", lambda: consent)

    result = main_mod.run()
    assert result == 1
    assert consent.closed if hasattr(consent, "closed") else True


def test_run_persists_consent_and_calls_menu(monkeypatch):
    consent = SimpleNamespace(has_external_consent=True, has_data_consent=True)
    consent.ask_for_consent = lambda: True
    monkeypatch.setattr(main_mod, "UserConsent", lambda: consent)

    loader = SimpleNamespace()
    loader.load = lambda: {"cfg": True}
    monkeypatch.setattr(main_mod, "ConfigLoader", lambda: loader)

    cfg_obj = SimpleNamespace(
        save_with_consent=lambda *args, **kwargs: None,
        save_config=lambda: None,
    )
    monkeypatch.setattr(main_mod, "configuration_for_users", lambda data: cfg_obj)

    ctx = DummyContext()
    monkeypatch.setattr(main_mod, "create_app_context", lambda **kwargs: ctx)

    menu_calls = {}

    def fake_menu(context):
        menu_calls["called_with"] = context
        return 0

    monkeypatch.setattr(main_mod, "main_menu", fake_menu)

    result = main_mod.run()

    assert result == 0
    assert menu_calls["called_with"] is ctx
    assert ctx.closed is True


def test_run_closes_context_when_menu_raises(monkeypatch):
    consent = SimpleNamespace(has_external_consent=False, has_data_consent=False)
    consent.ask_for_consent = lambda: True
    monkeypatch.setattr(main_mod, "UserConsent", lambda: consent)

    loader = SimpleNamespace()
    loader.load = lambda: {}
    monkeypatch.setattr(main_mod, "ConfigLoader", lambda: loader)

    cfg_obj = SimpleNamespace(
        save_with_consent=lambda *args, **kwargs: None,
        save_config=lambda: None,
    )
    monkeypatch.setattr(main_mod, "configuration_for_users", lambda data: cfg_obj)

    ctx = DummyContext()
    monkeypatch.setattr(main_mod, "create_app_context", lambda **kwargs: ctx)

    def boom(_):
        raise RuntimeError("menu failed")

    monkeypatch.setattr(main_mod, "main_menu", boom)

    with pytest.raises(RuntimeError):
        main_mod.run()

    assert ctx.closed is True

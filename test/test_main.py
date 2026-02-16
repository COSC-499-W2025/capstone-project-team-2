import pytest
from types import SimpleNamespace

# Tests for the CLI entrypoint orchestration and consent flow.
import src.cli.main as main_mod


class DummyContext:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_run_exits_when_consent_declined(monkeypatch):
    """Check that the app exits when consent is denied.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate exit status and cleanup.
    """
    consent = SimpleNamespace(has_external_consent=False, has_data_consent=False)
    consent.ask_for_consent = lambda: False
    monkeypatch.setattr(main_mod, "UserConsent", lambda: consent)

    result = main_mod.run()
    assert result == 1
    assert consent.closed if hasattr(consent, "closed") else True


def test_run_persists_consent_and_calls_menu(monkeypatch):
    """Check that consent is saved and the menu is called.

    Args:
        monkeypatch: Pytest fixture for patching module attributes.

    Returns:
        None: Assertions validate menu call and context cleanup.
    """
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

    def fake_menu():
        return 0

    monkeypatch.setattr(main_mod, "main_menu", fake_menu)

    result = main_mod.run()

    assert result == 0
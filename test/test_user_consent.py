from pathlib import Path

import pytest

from src.config.user_consent import UserConsent, consent_document_path, read_consent_file


def test_default_consents_are_false():
    uc = UserConsent()
    assert uc.check_consent() == (False, False)


def test_set_consent_allows_data_only():
    uc = UserConsent()
    uc.set_consent(data_consent=True, external_consent=False)
    assert uc.check_consent() == (True, False)


def test_set_consent_allows_data_and_external():
    uc = UserConsent()
    uc.set_consent(data_consent=True, external_consent=True)
    assert uc.check_consent() == (True, True)


def test_set_consent_rejects_external_without_data():
    uc = UserConsent()
    with pytest.raises(ValueError):
        uc.set_consent(data_consent=False, external_consent=True)


def test_revoke_consent_defaults_to_both():
    uc = UserConsent(has_data_consent=True, has_external_consent=True)
    uc.revoke_consent()
    assert uc.check_consent() == (False, False)


def test_revoke_data_only_keeps_external_state():
    uc = UserConsent(has_data_consent=True, has_external_consent=True)
    uc.revoke_consent(include_external=False)
    assert uc.check_consent() == (False, True)


def test_consent_document_path_points_to_repo_file():
    path = consent_document_path()
    assert path.name == "consent_document.md"
    assert isinstance(path, Path)


def test_read_consent_file_returns_content():
    content = read_consent_file()
    assert isinstance(content, str)
    assert len(content) > 0


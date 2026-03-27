from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def consent_document_path() -> Path:
    """
    Return the repository-level consent document path.
    """
    return Path(__file__).resolve().parents[2] / "consent_document.md"


def read_consent_file() -> str:
    """
    Load the consent document text.

    Returns:
        str: File contents.

    Raises:
        FileNotFoundError: If consent_document.md is missing.
    """
    return consent_document_path().read_text(encoding="utf-8")


@dataclass
class UserConsent:
    """
    Non-interactive consent state container for web/API flows.
    """

    has_data_consent: bool = False
    has_external_consent: bool = False

    def set_consent(self, *, data_consent: bool, external_consent: bool) -> None:
        """
        Set both consent states with consistency checks.

        Args:
            data_consent: Permission for local data processing.
            external_consent: Permission for external services.

        Raises:
            ValueError: If external consent is true while data consent is false.
        """
        if external_consent and not data_consent:
            raise ValueError("External consent requires data consent.")
        self.has_data_consent = data_consent
        self.has_external_consent = external_consent

    def check_consent(self) -> tuple[bool, bool]:
        """
        Return current consent state as (data_consent, external_consent).
        """
        return self.has_data_consent, self.has_external_consent

    def revoke_consent(self, include_external: bool = True) -> None:
        """
        Revoke previously granted consent.
        """
        self.has_data_consent = False
        if include_external:
            self.has_external_consent = False


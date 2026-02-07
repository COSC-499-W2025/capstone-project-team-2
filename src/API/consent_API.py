"""FastAPI endpoints for storing user privacy consent."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config.Configuration import configuration_for_users
from src.config.user_startup_config import ConfigLoader
from src.core.app_context import runtimeAppContext

class PrivacyConsentRequest(BaseModel):
    """
    Request payload for updating stored privacy consent flags.

    Args:
        data_consent: Whether the user consents to data usage.
        external_consent: Whether the user consents to external services.
    """

    data_consent: bool
    external_consent: bool = False

consentRouter = APIRouter()

@consentRouter.post("/privacy-consent")
def update_privacy_consent(payload: PrivacyConsentRequest) -> dict:
    """
    Persist privacy consent to config storage and update runtime settings.

    Args:
        payload: Consent flags from the client.

    Returns:
        dict: The saved consent values.
    """
    if payload.external_consent and not payload.data_consent:
        raise HTTPException(
            status_code=400,
            detail="External consent requires data consent to be enabled.",
        )

    try:
        cfg = ConfigLoader().load()
        configure_json = configuration_for_users(cfg)
        configure_json.save_with_consent(
            payload.external_consent,
            payload.data_consent,
        )
        configure_json.save_config()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist consent: {exc}",
        )

    runtimeAppContext.external_consent = payload.external_consent
    runtimeAppContext.data_consent = payload.data_consent
    return {
        "data_consent": payload.data_consent,
        "external_consent": payload.external_consent,
    }

@consentRouter.post("/config/update")
def update_config_file(config: dict):
    config_saver = configuration_for_users(config)
    config_saver.save_config()

@consentRouter.get("/config/get")
def get_config_dict() -> dict:
    try:
        return ConfigLoader().load()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=e
        )
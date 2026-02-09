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

    runtimeAppContext.external_consent = payload.external_consent
    runtimeAppContext.data_consent = payload.data_consent

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

    return {
        "data_consent": payload.data_consent,
        "external_consent": payload.external_consent,
    }

@consentRouter.post("/config/update")
def update_config_file(config: dict):
    """
    Savses a dictionary as the configuration file 

    API call is /config/update

    Args:
        dict: dictionary of the config file to save

    Returns:
        None

    Raises:
        Raises an HTTP exception of status 500 when config fails to save in any capacity
    """
    try:
        config_saver = configuration_for_users(config)
        config_saver.save_config()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=e
        )

@consentRouter.get("/config/get")
def get_config_dict() -> dict:
    """
    Gets a dictionary of the user conifguration file

    API call is /config/get

    Args:
        None

    Returns:
        dict: dictionary of the config file

    Raises:
        Raises an HTTP exception of status 500 when config fails to load in any capacity
    """
    try:
        return ConfigLoader().load()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=e
        )
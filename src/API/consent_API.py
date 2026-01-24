from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config.Configuration import configuration_for_users
from src.config.user_startup_config import ConfigLoader
from src.core.app_context import runtimeAppContext

class PrivacyConsentRequest(BaseModel):
    data_consent: bool
    external_consent: bool = False

consentRouter = APIRouter()

@consentRouter.post("/privacy-consent")
def update_privacy_consent(payload: PrivacyConsentRequest) -> dict:
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
        ) from exc

    runtimeAppContext.external_consent = payload.external_consent
    return {
        "data_consent": payload.data_consent,
        "external_consent": payload.external_consent,
    }
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import db
from app.db import models
from app import schema
from app.core.auth import get_current_user
from app.core.model_registry import AVAILABLE_MODELS, PROVIDERS, MAX_ACTIVE_MODELS, DEFAULT_ACTIVE_MODELS

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


def _require_admin(user: models.User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")


def _get_or_create_settings(session: Session) -> models.SystemSettings:
    settings = session.query(models.SystemSettings).first()
    if not settings:
        settings = models.SystemSettings(
            api_keys={},
            active_models=DEFAULT_ACTIVE_MODELS,
        )
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.get("/settings")
def get_settings(
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    _require_admin(current_user)
    settings = _get_or_create_settings(session)

    masked_keys = {}
    for prov, key in (settings.api_keys or {}).items():
        if key:
            masked_keys[prov] = key[:4] + "***" + key[-4:] if len(key) > 8 else "***"
        else:
            masked_keys[prov] = ""

    return {
        "api_keys": masked_keys,
        "active_models": settings.active_models or [],
        "available_models": AVAILABLE_MODELS,
        "providers": list(PROVIDERS.keys()),
    }


@router.post("/settings/update")
def update_settings(
    payload: schema.SystemSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    _require_admin(current_user)

    if payload.active_models and len(payload.active_models) > MAX_ACTIVE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"You can only activate up to {MAX_ACTIVE_MODELS} LLMs at once.",
        )

    if payload.active_models:
        unknown = [m for m in payload.active_models if m not in AVAILABLE_MODELS]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown model(s): {unknown}. Available: {list(AVAILABLE_MODELS.keys())}",
            )

    settings = _get_or_create_settings(session)

    if payload.api_keys is not None:
        # Merge new keys into existing (don't overwrite keys not included)
        existing = settings.api_keys or {}
        existing.update({k: v for k, v in payload.api_keys.items() if v})
        settings.api_keys = existing

    if payload.active_models is not None:
        settings.active_models = payload.active_models

    session.commit()
    return {"message": "Settings updated successfully"}


@router.get("/models")
def list_available_models(
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    settings = _get_or_create_settings(session)
    return {
        "available_models": AVAILABLE_MODELS,
        "active_models": settings.active_models or [],
    }
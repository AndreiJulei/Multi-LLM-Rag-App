from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import db
from app.core.auth import get_current_user
from app.core.model_registry import AVAILABLE_MODELS

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("/active-models")
def get_active_models(
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    settings = session.query(models.SystemSettings).first()
    active = settings.active_models if settings else []
    return {
        "active_models": active,
        "available_models": AVAILABLE_MODELS,
    }
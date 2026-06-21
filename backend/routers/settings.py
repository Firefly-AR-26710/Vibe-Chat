from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from database import get_db
import models

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"]
)

class LLMSettings(BaseModel):
    provider: str
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = ""
    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    anthropic_model: str = ""

@router.get("/llm", response_model=LLMSettings)
def get_llm_settings(db: Session = Depends(get_db)):
    settings_records = db.query(models.SystemSettings).all()
    settings_dict = {record.key: record.value for record in settings_records}
    
    return LLMSettings(
        provider=settings_dict.get("LLM_PROVIDER", "openai"),
        openai_api_key=settings_dict.get("OPENAI_API_KEY", ""),
        openai_base_url=settings_dict.get("OPENAI_BASE_URL", ""),
        openai_model=settings_dict.get("OPENAI_MODEL", ""),
        anthropic_api_key=settings_dict.get("ANTHROPIC_API_KEY", ""),
        anthropic_base_url=settings_dict.get("ANTHROPIC_BASE_URL", ""),
        anthropic_model=settings_dict.get("ANTHROPIC_MODEL", ""),
    )

@router.post("/llm")
def update_llm_settings(settings: LLMSettings, db: Session = Depends(get_db)):
    settings_dict = {
        "LLM_PROVIDER": settings.provider,
        "OPENAI_API_KEY": settings.openai_api_key,
        "OPENAI_BASE_URL": settings.openai_base_url,
        "OPENAI_MODEL": settings.openai_model,
        "ANTHROPIC_API_KEY": settings.anthropic_api_key,
        "ANTHROPIC_BASE_URL": settings.anthropic_base_url,
        "ANTHROPIC_MODEL": settings.anthropic_model,
    }
    
    for key, value in settings_dict.items():
        record = db.query(models.SystemSettings).filter(models.SystemSettings.key == key).first()
        if record:
            record.value = value
        else:
            new_record = models.SystemSettings(key=key, value=value)
            db.add(new_record)
            
    db.commit()
    return {"message": "Settings updated successfully"}

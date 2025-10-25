# backend/models/user_settings_model.py
from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


class UserSettingsIn(BaseModel):
    language: Literal["es", "en"] = "es"
    theme: Literal["light", "dark"] = "light"
    fontScale: float = Field(default=1.0, ge=0.5, le=2.0)
    highContrast: bool = False


class UserSettingsOut(UserSettingsIn):
    user_id: str


class UserSettingsDB(UserSettingsIn):
    user_id: str

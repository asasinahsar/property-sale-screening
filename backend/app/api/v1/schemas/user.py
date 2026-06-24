import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    login_email: EmailStr
    password: str
    role: Literal["analyst", "manager"]


class UserUpdate(BaseModel):
    role: Literal["analyst", "manager"] | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    login_email: str
    role: str
    failed_login_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

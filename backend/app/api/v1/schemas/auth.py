import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    login_email: EmailStr
    password: str


class MeResponse(BaseModel):
    id: uuid.UUID
    login_email: str
    role: str

    model_config = {"from_attributes": True}


class DashboardKpiResponse(BaseModel):
    total_companies: int
    high_score_companies: int
    avg_score: float
    event_count: int

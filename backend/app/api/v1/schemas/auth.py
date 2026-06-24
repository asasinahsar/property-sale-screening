from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    login_email: EmailStr
    password: str

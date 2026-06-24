from fastapi import APIRouter, Depends

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.user import UserResponse
from app.models.user import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

"""直近イベントエンドポイント."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.api.v1.schemas.event import RecentEventSchema
from app.core.dependencies import get_db
from app.models.user import User
from app.repositories.event_repository import EventRepository

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("/recent", response_model=list[RecentEventSchema])
async def get_recent_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecentEventSchema]:
    """直近 7 日のイベントを occurred_at 降順で最大 10 件返す."""
    rows = await EventRepository(db).get_recent(days=7, limit=10)
    return [
        RecentEventSchema(
            company_id=company.id,
            securities_code=company.securities_code,
            company_name=company.name,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            event_score=float(event_score) if event_score is not None else None,
        )
        for event, company, event_score in rows
    ]

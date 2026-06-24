"""Phase 2 テーブル: hitl_labels / watchlist_items / notifications"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

HitlLabel = Enum("hit", "miss", name="hitl_label")
TriggerType = Enum(
    "score_threshold",
    "new_disclosure",
    "large_shareholding",
    name="notification_trigger_type",
)


class HitlLabelRecord(Base):
    __tablename__ = "hitl_labels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(HitlLabel, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    notify_conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notify_channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="watchlist_item"
    )

    __table_args__ = (
        Index("uq_watchlist_items_user_company", "user_id", "company_id", unique=True),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    watchlist_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlist_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_type: Mapped[str] = mapped_column(TriggerType, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    watchlist_item: Mapped["WatchlistItem"] = relationship(
        back_populates="notifications"
    )

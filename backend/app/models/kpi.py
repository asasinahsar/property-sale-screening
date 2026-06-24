import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin

TaskType = Enum(
    "primary_screening",
    "deep_dive",
    "report",
    "other",
    name="task_type",
)


class WorkLog(Base):
    __tablename__ = "work_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    task_type: Mapped[str] = mapped_column(TaskType, nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    screening_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    period_label: Mapped[str | None] = mapped_column(nullable=True)
    logged_on: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    __table_args__ = (
        Index("idx_work_logs_logged_on", "logged_on"),
        Index("idx_work_logs_user_id", "user_id"),
    )


class KpiSnapshot(TimestampMixin, Base):
    __tablename__ = "kpi_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)
    universe_coverage: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    traceability_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    avg_structure_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    reproducibility_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    total_workload_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    workload_reduction_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    __table_args__ = (Index("idx_kpi_snapshots_period", "period_from", "period_to"),)

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

RunStatus = Enum("running", "success", "failed", name="run_status")
Confidence = Enum("high", "mid", "low", name="confidence_level")
ParamKind = Enum("calibrated", "hitl_updated", name="param_kind")


class ScreeningRun(Base):
    __tablename__ = "screening_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(RunStatus, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scoring_results: Mapped[list["ScoringResult"]] = relationship(
        back_populates="screening_run"
    )

    __table_args__ = (
        Index("idx_screening_runs_is_current_status", "is_current", "status"),
    )


class ScoringResult(TimestampMixin, Base):
    __tablename__ = "scoring_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    screening_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    structure_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    event_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    total_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    event_boost: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    confidence: Mapped[str] = mapped_column(Confidence, nullable=False)
    ai_judgment: Mapped[str | None] = mapped_column(Text, nullable=True)
    judgment_refs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prev_total_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    screening_run: Mapped["ScreeningRun"] = relationship(
        back_populates="scoring_results"
    )

    __table_args__ = (
        Index(
            "uq_scoring_results_run_company",
            "screening_run_id",
            "company_id",
            unique=True,
        ),
        Index("idx_scoring_results_run_id", "screening_run_id"),
        Index("idx_scoring_results_total_score", "total_score"),
    )


class ScoringParameters(TimestampMixin, Base):
    __tablename__ = "scoring_parameters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    param_kind: Mapped[str] = mapped_column(ParamKind, nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    backtest_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

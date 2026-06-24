import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

DocumentType = Enum(
    "yuho",
    "mid_term_plan",
    "timely_disclosure",
    "large_shareholding",
    name="document_type",
)
SignalType = Enum(
    "activist_proposal",
    "capital_efficiency_target",
    "sale_suggestion",
    "other",
    name="signal_type",
)
SignalStance = Enum("support", "counter", name="signal_stance")
EventType = Enum("new_disclosure", "large_shareholding", name="event_type")


class Company(TimestampMixin, Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    securities_code: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    market_cap: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    is_universe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    financial_data: Mapped[list["FinancialData"]] = relationship(
        back_populates="company"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="company")
    qualitative_signals: Mapped[list["QualitativeSignal"]] = relationship(
        back_populates="company"
    )
    events: Mapped[list["Event"]] = relationship(back_populates="company")

    __table_args__ = (
        Index("idx_companies_securities_code", "securities_code"),
        Index("idx_companies_industry", "industry"),
    )


class FinancialData(Base):
    __tablename__ = "financial_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    revenue: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    pbr: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    adjusted_pbr: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    equity_ratio: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    re_market_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    re_book_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    unrealized_gain: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    unrealized_gain_ratio: Mapped[float | None] = mapped_column(
        Numeric(8, 4), nullable=True
    )
    roic: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    wacc: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    stock_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="financial_data")

    __table_args__ = (
        Index(
            "uq_financial_data_company_date", "company_id", "as_of_date", unique=True
        ),
    )


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(DocumentType, nullable=False)
    s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    disclosed_at: Mapped[date] = mapped_column(Date, nullable=False)

    company: Mapped["Company"] = relationship(back_populates="documents")
    qualitative_signals: Mapped[list["QualitativeSignal"]] = relationship(
        back_populates="document"
    )
    events: Mapped[list["Event"]] = relationship(back_populates="document")


class QualitativeSignal(Base):
    __tablename__ = "qualitative_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    signal_type: Mapped[str] = mapped_column(SignalType, nullable=False)
    stance: Mapped[str] = mapped_column(SignalStance, nullable=False)
    strength: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    recency: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_page: Mapped[int] = mapped_column(Integer, nullable=False)
    quote_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    company: Mapped["Company"] = relationship(back_populates="qualitative_signals")
    document: Mapped["Document"] = relationship(back_populates="qualitative_signals")

    __table_args__ = (
        Index("idx_qualitative_signals_company_id", "company_id"),
        Index("idx_qualitative_signals_document_id", "document_id"),
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(EventType, nullable=False)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    company: Mapped["Company"] = relationship(back_populates="events")
    document: Mapped["Document"] = relationship(back_populates="events")

    __table_args__ = (
        Index("idx_events_occurred_at", "occurred_at"),
        Index("idx_events_company_id", "company_id"),
    )

"""Série temporal (TimescaleDB hypertable) — métricas agregadas por produto."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ProductMetricModel(Base):
    __tablename__ = "product_metrics"

    bucket: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

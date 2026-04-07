"""Série temporal em `product_metrics` (TimescaleDB hypertable)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ProductMetricModel


class ProductMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_add(
        self,
        *,
        product_id: UUID,
        bucket: datetime,
        views_delta: int,
        revenue_delta: Decimal,
    ) -> None:
        ins = insert(ProductMetricModel).values(
            bucket=bucket,
            product_id=product_id,
            views=views_delta,
            revenue=revenue_delta,
        )
        stmt = ins.on_conflict_do_update(
            index_elements=["bucket", "product_id"],
            set_={
                "views": ProductMetricModel.views + ins.excluded.views,
                "revenue": ProductMetricModel.revenue + ins.excluded.revenue,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def list_for_product(
        self,
        product_id: UUID,
        *,
        from_bucket: datetime,
        to_bucket: datetime,
    ) -> list[ProductMetricModel]:
        stmt = (
            select(ProductMetricModel)
            .where(
                ProductMetricModel.product_id == product_id,
                ProductMetricModel.bucket >= from_bucket,
                ProductMetricModel.bucket <= to_bucket,
            )
            .order_by(ProductMetricModel.bucket.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_bucket(self, product_id: UUID, bucket: datetime) -> ProductMetricModel | None:
        stmt = select(ProductMetricModel).where(
            ProductMetricModel.product_id == product_id,
            ProductMetricModel.bucket == bucket,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

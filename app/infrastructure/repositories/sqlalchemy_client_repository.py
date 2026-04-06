from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Client
from app.infrastructure.database.models import ClientModel


def _to_domain(row: ClientModel) -> Client:
    return Client(
        id=row.id,
        legal_name=row.legal_name,
        trade_name=row.trade_name,
        email=row.email,
        phone=row.phone,
        document=row.document,
        segment=row.segment,
        city=row.city,
        country=row.country,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(self, offset: int, limit: int) -> list[Client]:
        stmt = (
            select(ClientModel).order_by(ClientModel.created_at.desc()).offset(offset).limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_domain(r) for r in result.scalars().all()]

    async def get_by_id(self, client_id: UUID) -> Client | None:
        row = await self._session.get(ClientModel, client_id)
        return _to_domain(row) if row else None

    async def create(
        self,
        *,
        legal_name: str,
        trade_name: str | None,
        email: str,
        phone: str | None,
        document: str,
        segment: str | None,
        city: str | None,
        country: str,
    ) -> Client:
        model = ClientModel(
            legal_name=legal_name,
            trade_name=trade_name,
            email=email,
            phone=phone,
            document=document,
            segment=segment,
            city=city,
            country=country,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

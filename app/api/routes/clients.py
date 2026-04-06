from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domain.entities import User
from app.infrastructure.repositories import SQLAlchemyClientRepository
from app.schemas.client import ClientCreate, ClientRead

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
async def list_clients(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[ClientRead]:
    repo = SQLAlchemyClientRepository(session)
    items = await repo.list_paginated(offset=offset, limit=limit)
    return [
        ClientRead(
            id=c.id,
            legal_name=c.legal_name,
            trade_name=c.trade_name,
            email=c.email,
            phone=c.phone,
            document=c.document,
            segment=c.segment,
            city=c.city,
            country=c.country,
            created_at=c.created_at,
        )
        for c in items
    ]


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ClientRead:
    repo = SQLAlchemyClientRepository(session)
    c = await repo.create(
        legal_name=body.legal_name,
        trade_name=body.trade_name,
        email=body.email.lower(),
        phone=body.phone,
        document=body.document,
        segment=body.segment,
        city=body.city,
        country=body.country,
    )
    await session.commit()
    return ClientRead(
        id=c.id,
        legal_name=c.legal_name,
        trade_name=c.trade_name,
        email=c.email,
        phone=c.phone,
        document=c.document,
        segment=c.segment,
        city=c.city,
        country=c.country,
        created_at=c.created_at,
    )

from typing import Protocol
from uuid import UUID

from app.domain.entities import Client


class ClientRepository(Protocol):
    async def list_paginated(self, offset: int, limit: int) -> list[Client]: ...

    async def get_by_id(self, client_id: UUID) -> Client | None: ...

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
    ) -> Client: ...

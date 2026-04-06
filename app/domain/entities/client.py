from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Client:
    id: UUID
    legal_name: str
    trade_name: str | None
    email: str
    phone: str | None
    document: str  # CPF/CNPJ ou equivalente
    segment: str | None
    city: str | None
    country: str
    created_at: datetime
    updated_at: datetime

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class User:
    id: UUID
    email: str
    full_name: str
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

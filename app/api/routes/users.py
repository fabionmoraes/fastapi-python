from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domain.entities import User
from app.infrastructure.repositories import SQLAlchemyUserRepository
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(current: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead(
        id=current.id,
        email=current.email,
        full_name=current.full_name,
        is_active=current.is_active,
        created_at=current.created_at,
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    """Criação de usuário (alternativa ao /auth/register sem JWT)."""
    from app.core.security import hash_password

    repo = SQLAlchemyUserRepository(session)
    if await repo.get_by_email(body.email.lower()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email exists")
    user = await repo.create(
        email=body.email.lower(),
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
    )
    await session.commit()
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )

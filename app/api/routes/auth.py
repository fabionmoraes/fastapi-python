from typing import Annotated

from arq import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_arq_pool, get_auth_service, get_db
from app.domain.services import AuthService
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
    pool: Annotated[ArqRedis, Depends(get_arq_pool)],
) -> TokenResponse:
    try:
        user = await auth.register(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    await session.commit()
    await pool.enqueue_job("send_welcome_email_task", email=user.email, name=user.full_name)
    token = auth.issue_token(user)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    try:
        user = await auth.authenticate(email=body.email, password=body.password)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        ) from None
    token = auth.issue_token(user)
    return TokenResponse(access_token=token)

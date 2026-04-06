from app.core.security import create_access_token, hash_password, verify_password
from app.domain.entities import User
from app.domain.repositories import UserRepository


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
    ) -> User:
        existing = await self._users.get_by_email(email.lower())
        if existing:
            raise ValueError("email already registered")
        return await self._users.create(
            email=email.lower(),
            full_name=full_name,
            hashed_password=hash_password(password),
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._users.get_by_email(email.lower())
        if not user or not user.is_active:
            raise ValueError("invalid credentials")
        if not verify_password(password, user.hashed_password):
            raise ValueError("invalid credentials")
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(str(user.id), extra={"email": user.email})

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole, UserStatus
from app.models.patient import PatientProfile
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedError, ConflictError
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def register_patient(self, email, password, first_name, last_name, phone=None):
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ConflictError("Email already registered")
        user = User(
            email=email, password_hash=hash_password(password),
            role=UserRole.PATIENT.value, status=UserStatus.ACTIVE.value,
            first_name=first_name, last_name=last_name, phone=phone,
        )
        self.db.add(user)
        await self.db.flush()
        profile = PatientProfile(user_id=user.id)
        self.db.add(profile)
        await self.db.flush()
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token
    async def login(self, email, password):
        result = await self.db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if user.status == UserStatus.BLOCKED.value:
            raise UnauthorizedError("Account is blocked. Contact admin.")
        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token
    async def refresh(self, refresh_token_str):
        try:
            payload = decode_token(refresh_token_str)
        except ValueError:
            raise UnauthorizedError("Invalid refresh token")
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid token type")
        user_id = payload["sub"]
        result = await self.db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedError("User not found")
        new_access = create_access_token(user.id, user.role)
        new_refresh = create_refresh_token(user.id)
        return new_access, new_refresh
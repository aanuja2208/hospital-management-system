from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User, UserRole, UserStatus
from app.models.doctor import DoctorProfile
from app.models.patient import PatientProfile
from app.core.exceptions import NotFoundError, ConflictError
from app.core.security import hash_password
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def get_user_by_id(self, user_id):
        result = await self.db.execute(select(User).where(User.id == str(user_id), User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        return user
    async def update_user(self, user, **kwargs):
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        await self.db.flush()
        return user
    async def update_user_status(self, user_id, status):
        user = await self.get_user_by_id(user_id)
        user.status = status.value if hasattr(status, 'value') else status
        await self.db.flush()
        return user
    async def list_users(self, page=1, per_page=20, role=None, search=None):
        query = select(User).where(User.deleted_at.is_(None))
        count_query = select(func.count()).select_from(User).where(User.deleted_at.is_(None))
        if role:
            role_val = role.value if hasattr(role, 'value') else role
            query = query.where(User.role == role_val)
            count_query = count_query.where(User.role == role_val)
        if search:
            p = f"%{search}%"
            filt = (User.first_name.ilike(p)) | (User.last_name.ilike(p)) | (User.email.ilike(p))
            query = query.where(filt)
            count_query = count_query.where(filt)
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * per_page).limit(per_page).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
    async def create_doctor(self, email, password, first_name, last_name, phone,
                           department_id, specialization, registration_number,
                           qualification, experience_years):
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ConflictError("Email already registered")
        user = User(
            email=email, password_hash=hash_password(password),
            role=UserRole.DOCTOR.value, status=UserStatus.ACTIVE.value,
            first_name=first_name, last_name=last_name, phone=phone,
        )
        self.db.add(user)
        await self.db.flush()
        profile = DoctorProfile(
            user_id=user.id, department_id=str(department_id),
            specialization=specialization, registration_number=registration_number,
            qualification=qualification, experience_years=experience_years,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
    async def search_global(self, query, entity_type=None):
        results = {"patients": [], "doctors": []}
        p = f"%{query}%"
        if not entity_type or entity_type == "patient":
            q = select(User).where(
                User.role == UserRole.PATIENT.value, User.deleted_at.is_(None),
                (User.first_name.ilike(p)) | (User.last_name.ilike(p)) | (User.email.ilike(p))
            ).limit(20)
            res = await self.db.execute(q)
            results["patients"] = list(res.scalars().all())
        if not entity_type or entity_type == "doctor":
            q = select(DoctorProfile).join(User).where(
                User.deleted_at.is_(None),
                (User.first_name.ilike(p)) | (User.last_name.ilike(p)) | (DoctorProfile.specialization.ilike(p))
            ).limit(20)
            res = await self.db.execute(q)
            results["doctors"] = list(res.scalars().all())
        return results
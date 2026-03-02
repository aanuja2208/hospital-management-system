from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserUpdateRequest
from app.schemas.patient import PatientUpdateRequest
from app.services.user_service import UserService
from app.core.permissions import get_current_user
from app.models.user import User
router = APIRouter(prefix="/users", tags=["Users"])
@router.get("/me")
async def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id), "email": user.email, "role": user.role,
        "status": user.status, "first_name": user.first_name,
        "last_name": user.last_name, "phone": user.phone,
    }
@router.put("/me")
async def update_profile(
    req: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = UserService(db)
    updated = await svc.update_user(user, **req.model_dump(exclude_unset=True))
    return {
        "id": str(updated.id), "email": updated.email, "role": updated.role,
        "status": updated.status, "first_name": updated.first_name,
        "last_name": updated.last_name, "phone": updated.phone,
    }
@router.put("/me/patient-profile")
async def update_patient_profile(
    req: PatientUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role != "PATIENT" or not user.patient_profile:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Only patients can update patient profile")
    profile = user.patient_profile
    for key, value in req.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(profile, key, value)
    await db.flush()
    return {
        "id": str(profile.id), "user_id": str(profile.user_id),
        "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
        "gender": profile.gender, "blood_group": profile.blood_group,
        "address": profile.address, "emergency_contact": profile.emergency_contact,
        "insurance_id": profile.insurance_id,
    }
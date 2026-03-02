from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import AuthService
from app.core.permissions import get_current_user
from app.models.user import User
router = APIRouter(prefix="/auth", tags=["Authentication"])
@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    user, access, refresh = await svc.register_patient(
        email=req.email, password=req.password,
        first_name=req.first_name, last_name=req.last_name, phone=req.phone
    )
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    user, access, refresh = await svc.login(email=req.email, password=req.password)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
@router.post("/refresh")
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    access, refresh = await svc.refresh(req.refresh_token)
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    result = {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "phone": current_user.phone,
    }
    if current_user.doctor_profile:
        result["doctor_profile"] = {
            "id": str(current_user.doctor_profile.id),
            "specialization": current_user.doctor_profile.specialization,
            "department_id": str(current_user.doctor_profile.department_id),
        }
    if current_user.patient_profile:
        result["patient_profile"] = {
            "id": str(current_user.patient_profile.id),
        }
    return result
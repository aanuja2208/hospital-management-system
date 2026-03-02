from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.schemas.user import UserResponse, UserStatusUpdate
from app.schemas.doctor import DoctorCreateRequest, DoctorResponse
from app.services.user_service import UserService
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.core.permissions import require_admin
from app.models.user import User
from app.models.doctor import DoctorProfile
from app.models.department import Department
router = APIRouter(prefix="/admin", tags=["Admin"])
@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = UserService(db)
    users, total = await svc.list_users(page, per_page, role, search)
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "status": u.status,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "phone": u.phone,
                "created_at": str(u.created_at) if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    req: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = UserService(db)
    audit = AuditService(db)
    user = await svc.update_user_status(user_id, req.status)
    await audit.log(admin.id, "UPDATE_USER_STATUS", "User", user.id,
                    new_values={"status": req.status})
    return {
        "id": str(user.id), "email": user.email, "role": user.role,
        "status": user.status, "first_name": user.first_name,
        "last_name": user.last_name, "phone": user.phone,
    }
@router.post("/doctors", status_code=201)
async def onboard_doctor(
    req: DoctorCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = UserService(db)
    audit = AuditService(db)
    profile = await svc.create_doctor(
        email=req.email, password=req.password,
        first_name=req.first_name, last_name=req.last_name,
        phone=req.phone, department_id=req.department_id,
        specialization=req.specialization,
        registration_number=req.registration_number,
        qualification=req.qualification,
        experience_years=req.experience_years,
    )
    await audit.log(admin.id, "ONBOARD_DOCTOR", "DoctorProfile", profile.id,
                    new_values={"email": req.email, "specialization": req.specialization})
    return {
        "id": str(profile.id), "user_id": str(profile.user_id),
        "department_id": str(profile.department_id),
        "department_name": profile.department.name if profile.department else None,
        "specialization": profile.specialization,
        "registration_number": profile.registration_number,
        "qualification": profile.qualification,
        "experience_years": profile.experience_years,
        "status": profile.status,
        "first_name": profile.user.first_name if profile.user else None,
        "last_name": profile.user.last_name if profile.user else None,
        "email": profile.user.email if profile.user else None,
    }
@router.get("/dashboard")
async def admin_dashboard(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    appt_svc = AppointmentService(db)
    appointment_stats = await appt_svc.get_dashboard_stats()
    doctors_result = await db.execute(select(func.count()).select_from(DoctorProfile))
    patients_result = await db.execute(
        select(func.count()).select_from(User).where(User.role == "PATIENT")
    )
    depts_result = await db.execute(select(func.count()).select_from(Department))
    return {
        "appointments": appointment_stats,
        "total_doctors": doctors_result.scalar() or 0,
        "total_patients": patients_result.scalar() or 0,
        "total_departments": depts_result.scalar() or 0,
    }
@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    action: str | None = None,
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = AuditService(db)
    logs, total = await svc.list_logs(page, per_page, action, entity_type)
    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "user_name": log.user.full_name if log.user else None,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id) if log.entity_id else None,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": log.ip_address,
                "created_at": str(log.created_at) if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }
@router.get("/search")
async def global_search(
    q: str = Query("", min_length=0),
    entity_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    svc = UserService(db)
    if not q:
        return {"patients": [], "doctors": []}
    results = await svc.search_global(q, entity_type)
    return {
        "patients": [
            {
                "id": str(p.id), "email": p.email, "first_name": p.first_name,
                "last_name": p.last_name, "role": p.role, "status": p.status,
            }
            for p in results["patients"]
        ],
        "doctors": [
            {
                "id": str(d.id),
                "name": d.user.full_name if d.user else None,
                "specialization": d.specialization,
                "department": d.department.name if d.department else None,
                "status": d.status,
            }
            for d in results["doctors"]
        ],
    }
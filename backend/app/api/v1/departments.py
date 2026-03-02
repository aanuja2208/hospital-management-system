from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.department import DepartmentCreateRequest, DepartmentUpdateRequest
from app.core.permissions import require_admin, require_any_authenticated
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.department import Department
router = APIRouter(prefix="/departments", tags=["Departments"])
def _format_dept(dept):
    return {
        "id": str(dept.id),
        "name": dept.name,
        "description": dept.description,
        "is_active": dept.is_active,
        "doctor_count": len(dept.doctors) if dept.doctors else 0,
        "created_at": str(dept.created_at) if dept.created_at else None,
    }
@router.get("/")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_authenticated),
):
    result = await db.execute(select(Department).order_by(Department.name))
    departments = result.scalars().all()
    return [_format_dept(d) for d in departments]
@router.post("/", status_code=201)
async def create_department(
    req: DepartmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    dept = Department(name=req.name, description=req.description)
    db.add(dept)
    await db.flush()
    await db.refresh(dept)
    return _format_dept(dept)
@router.put("/{dept_id}")
async def update_department(
    dept_id: str,
    req: DepartmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise NotFoundError("Department not found")
    if req.name is not None:
        dept.name = req.name
    if req.description is not None:
        dept.description = req.description
    if req.is_active is not None:
        dept.is_active = req.is_active
    await db.flush()
    return _format_dept(dept)
@router.get("/{dept_id}/doctors")
async def list_department_doctors(
    dept_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_any_authenticated),
):
    from app.models.doctor import DoctorProfile
    result = await db.execute(
        select(DoctorProfile).where(
            DoctorProfile.department_id == dept_id,
            DoctorProfile.status == "APPROVED"
        )
    )
    doctors = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "name": d.user.full_name if d.user else "Unknown",
            "specialization": d.specialization,
            "qualification": d.qualification,
            "experience_years": d.experience_years,
        }
        for d in doctors
    ]
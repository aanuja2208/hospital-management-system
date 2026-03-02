from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.schedule import ScheduleCreateRequest, ScheduleExceptionCreateRequest
from app.services.schedule_service import ScheduleService
from app.core.permissions import get_current_user, require_admin_or_doctor
from app.core.exceptions import ForbiddenError
from app.models.user import User
router = APIRouter(tags=["Schedules"])
def _format_schedule(s):
    return {
        "id": str(s.id), "doctor_id": str(s.doctor_id),
        "day_of_week": s.day_of_week, "start_time": s.start_time,
        "end_time": s.end_time, "slot_duration_minutes": s.slot_duration_minutes,
        "is_active": s.is_active, "effective_from": s.effective_from,
        "effective_until": s.effective_until,
    }
def _format_slot(s):
    return {
        "id": str(s.id), "doctor_id": str(s.doctor_id),
        "slot_date": s.slot_date, "start_time": s.start_time,
        "end_time": s.end_time, "is_booked": s.is_booked,
    }
@router.get("/doctors/{doctor_id}/schedules")
async def get_schedules(
    doctor_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_or_doctor),
):
    if user.role == "DOCTOR" and user.doctor_profile and str(user.doctor_profile.id) != doctor_id:
        raise ForbiddenError("Cannot view another doctor's schedules")
    svc = ScheduleService(db)
    schedules = await svc.get_doctor_schedules(doctor_id)
    return [_format_schedule(s) for s in schedules]
@router.post("/doctors/{doctor_id}/schedules", status_code=201)
async def create_schedule(
    doctor_id: str,
    req: ScheduleCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_or_doctor),
):
    if user.role == "DOCTOR" and user.doctor_profile and str(user.doctor_profile.id) != doctor_id:
        raise ForbiddenError("Cannot modify another doctor's schedule")
    svc = ScheduleService(db)
    schedule = await svc.create_schedule(
        doctor_id=doctor_id, day_of_week=req.day_of_week,
        start_time=req.start_time, end_time=req.end_time,
        slot_duration_minutes=req.slot_duration_minutes,
        effective_from=req.effective_from, effective_until=req.effective_until,
    )
    return _format_schedule(schedule)
@router.post("/doctors/{doctor_id}/exceptions", status_code=201)
async def add_exception(
    doctor_id: str,
    req: ScheduleExceptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin_or_doctor),
):
    if user.role == "DOCTOR" and user.doctor_profile and str(user.doctor_profile.id) != doctor_id:
        raise ForbiddenError("Cannot modify another doctor's schedule")
    svc = ScheduleService(db)
    exc = await svc.add_exception(
        doctor_id=doctor_id, exception_date=req.exception_date,
        reason=req.reason, notes=req.notes,
        is_available=req.is_available,
        start_time=req.start_time, end_time=req.end_time,
    )
    return {
        "id": str(exc.id), "doctor_id": str(exc.doctor_id),
        "exception_date": exc.exception_date, "reason": exc.reason,
        "notes": exc.notes, "is_available": exc.is_available,
    }
@router.get("/doctors/{doctor_id}/slots")
async def get_available_slots(
    doctor_id: str,
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if from_date is None:
        from_date = date.today().isoformat()
    if to_date is None:
        to_date = (date.today() + timedelta(days=14)).isoformat()
    svc = ScheduleService(db)
    slots = await svc.get_available_slots(doctor_id, from_date, to_date)
    return [_format_slot(s) for s in slots]
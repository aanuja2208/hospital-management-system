from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.appointment import AppointmentCreateRequest, AppointmentStatusUpdate, AppointmentReschedule
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.core.permissions import get_current_user, require_patient
from app.core.exceptions import ForbiddenError
from app.models.user import User
router = APIRouter(prefix="/appointments", tags=["Appointments"])
def _format_appointment(appt) -> dict:
    data = {
        "id": str(appt.id),
        "patient_id": str(appt.patient_id),
        "doctor_id": str(appt.doctor_id),
        "slot_id": str(appt.slot_id),
        "status": appt.status,
        "reason": appt.reason,
        "cancel_reason": appt.cancel_reason,
        "booked_at": str(appt.booked_at) if appt.booked_at else None,
        "confirmed_at": str(appt.confirmed_at) if appt.confirmed_at else None,
        "checked_in_at": str(appt.checked_in_at) if appt.checked_in_at else None,
        "started_at": str(appt.started_at) if appt.started_at else None,
        "completed_at": str(appt.completed_at) if appt.completed_at else None,
        "cancelled_at": str(appt.cancelled_at) if appt.cancelled_at else None,
    }
    if appt.patient and appt.patient.user:
        data["patient_name"] = appt.patient.user.full_name
    if appt.doctor and appt.doctor.user:
        data["doctor_name"] = appt.doctor.user.full_name
        data["specialization"] = appt.doctor.specialization
    if appt.slot:
        data["slot_date"] = appt.slot.slot_date
        data["slot_start_time"] = appt.slot.start_time
        data["slot_end_time"] = appt.slot.end_time
    return data
@router.post("/", status_code=201)
async def book_appointment(
    req: AppointmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_patient),
):
    svc = AppointmentService(db)
    audit = AuditService(db)
    appt = await svc.book(
        patient_id=user.patient_profile.id,
        doctor_id=req.doctor_id,
        slot_id=req.slot_id,
        reason=req.reason,
    )
    await audit.log(user.id, "BOOK_APPOINTMENT", "Appointment", appt.id)
    return _format_appointment(appt)
@router.get("/")
async def list_appointments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AppointmentService(db)
    patient_id = None
    doctor_id = None
    if user.role == "PATIENT" and user.patient_profile:
        patient_id = user.patient_profile.id
    elif user.role == "DOCTOR" and user.doctor_profile:
        doctor_id = user.doctor_profile.id
    appointments, total = await svc.list_appointments(
        page=page, per_page=per_page,
        patient_id=patient_id, doctor_id=doctor_id,
        status=status,
    )
    return {
        "items": [_format_appointment(a) for a in appointments],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AppointmentService(db)
    appt = await svc.get_appointment(appointment_id)
    if user.role == "PATIENT" and user.patient_profile:
        if appt.patient_id != user.patient_profile.id:
            raise ForbiddenError("Cannot access this appointment")
    elif user.role == "DOCTOR" and user.doctor_profile:
        if appt.doctor_id != user.doctor_profile.id:
            raise ForbiddenError("Cannot access this appointment")
    return _format_appointment(appt)
@router.patch("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: str,
    req: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AppointmentService(db)
    audit = AuditService(db)
    if req.status == "COMPLETED" and user.role not in ["DOCTOR", "ADMIN"]:
        raise ForbiddenError("Only doctor/admin can mark as completed")
    appt = await svc.transition_status(appointment_id, req.status, req.cancel_reason)
    await audit.log(user.id, "UPDATE_APPOINTMENT_STATUS", "Appointment", appt.id,
                    new_values={"status": req.status})
    return _format_appointment(appt)
@router.put("/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    req: AppointmentReschedule,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = AppointmentService(db)
    audit = AuditService(db)
    appt = await svc.reschedule(appointment_id, req.new_slot_id)
    await audit.log(user.id, "RESCHEDULE_APPOINTMENT", "Appointment", appt.id,
                    new_values={"new_slot_id": req.new_slot_id})
    return _format_appointment(appt)
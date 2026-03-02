from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.encounter import EncounterCreateRequest, PrescriptionCreateRequest
from app.services.encounter_service import EncounterService
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.core.permissions import get_current_user, require_doctor
from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.models.appointment import AppointmentStatus
router = APIRouter(tags=["Encounters"])
def _format_encounter(enc) -> dict:
    return {
        "id": str(enc.id),
        "appointment_id": str(enc.appointment_id),
        "doctor_id": str(enc.doctor_id),
        "patient_id": str(enc.patient_id),
        "chief_complaint": enc.chief_complaint,
        "diagnosis": enc.diagnosis,
        "clinical_notes": enc.clinical_notes,
        "follow_up_instructions": enc.follow_up_instructions,
        "encounter_date": str(enc.encounter_date) if enc.encounter_date else None,
        "prescriptions": [
            {
                "id": str(rx.id),
                "medication_name": rx.medication_name,
                "dosage": rx.dosage,
                "frequency": rx.frequency,
                "duration_days": rx.duration_days,
                "instructions": rx.instructions,
                "created_at": str(rx.created_at) if rx.created_at else None,
            }
            for rx in (enc.prescriptions or [])
        ],
    }
@router.post("/appointments/{appointment_id}/encounter", status_code=201)
async def create_encounter(
    appointment_id: str,
    req: EncounterCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_doctor),
):
    enc_svc = EncounterService(db)
    appt_svc = AppointmentService(db)
    audit = AuditService(db)
    encounter = await enc_svc.create_encounter(
        appointment_id=appointment_id,
        doctor_id=user.doctor_profile.id,
        chief_complaint=req.chief_complaint,
        diagnosis=req.diagnosis,
        clinical_notes=req.clinical_notes,
        follow_up_instructions=req.follow_up_instructions,
        prescriptions=[rx.model_dump() for rx in req.prescriptions],
    )
    await appt_svc.transition_status(appointment_id, AppointmentStatus.COMPLETED)
    await audit.log(user.id, "CREATE_ENCOUNTER", "Encounter", encounter.id)
    return _format_encounter(encounter)
@router.get("/encounters/{encounter_id}")
async def get_encounter(
    encounter_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = EncounterService(db)
    encounter = await svc.get_encounter(encounter_id)
    if user.role == "PATIENT" and user.patient_profile:
        if encounter.patient_id != user.patient_profile.id:
            raise ForbiddenError("Cannot access this encounter")
    elif user.role == "DOCTOR" and user.doctor_profile:
        if encounter.doctor_id != user.doctor_profile.id:
            raise ForbiddenError("Cannot access this encounter")
    return _format_encounter(encounter)
@router.get("/patients/{patient_id}/history")
async def get_patient_history(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == "PATIENT" and user.patient_profile:
        if str(user.patient_profile.id) != patient_id:
            raise ForbiddenError("Cannot access other patient's history")
    svc = EncounterService(db)
    encounters = await svc.get_patient_history(patient_id)
    return [_format_encounter(e) for e in encounters]
@router.post("/encounters/{encounter_id}/prescriptions", status_code=201)
async def add_prescription(
    encounter_id: str,
    req: PrescriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_doctor),
):
    svc = EncounterService(db)
    rx = await svc.add_prescription(
        encounter_id=encounter_id,
        medication_name=req.medication_name,
        dosage=req.dosage,
        frequency=req.frequency,
        duration_days=req.duration_days,
        instructions=req.instructions,
    )
    return {
        "id": str(rx.id), "medication_name": rx.medication_name,
        "dosage": rx.dosage, "frequency": rx.frequency,
        "duration_days": rx.duration_days, "instructions": rx.instructions,
    }
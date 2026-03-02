from typing import Any
from pydantic import BaseModel
from app.models.appointment import AppointmentStatus
class AppointmentCreateRequest(BaseModel):
    doctor_id: str
    slot_id: str
    reason: str | None = None
class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    slot_id: str
    status: str
    reason: str | None = None
    cancel_reason: str | None = None
    booked_at: Any = None
    confirmed_at: Any = None
    checked_in_at: Any = None
    started_at: Any = None
    completed_at: Any = None
    cancelled_at: Any = None
    patient_name: str | None = None
    doctor_name: str | None = None
    specialization: str | None = None
    slot_date: str | None = None
    slot_start_time: str | None = None
    slot_end_time: str | None = None
    model_config = {"from_attributes": True}
class AppointmentStatusUpdate(BaseModel):
    status: str
    cancel_reason: str | None = None
class AppointmentReschedule(BaseModel):
    new_slot_id: str
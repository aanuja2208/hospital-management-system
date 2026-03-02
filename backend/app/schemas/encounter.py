from typing import Any
from pydantic import BaseModel
class PrescriptionCreateRequest(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: str | None = None
class PrescriptionResponse(BaseModel):
    id: str
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: str | None = None
    created_at: Any = None
    model_config = {"from_attributes": True}
class EncounterCreateRequest(BaseModel):
    chief_complaint: str | None = None
    diagnosis: str | None = None
    clinical_notes: str | None = None
    follow_up_instructions: str | None = None
    prescriptions: list[PrescriptionCreateRequest] = []
class EncounterResponse(BaseModel):
    id: str
    appointment_id: str
    doctor_id: str
    patient_id: str
    chief_complaint: str | None = None
    diagnosis: str | None = None
    clinical_notes: str | None = None
    follow_up_instructions: str | None = None
    encounter_date: Any = None
    prescriptions: list[PrescriptionResponse] = []
    model_config = {"from_attributes": True}
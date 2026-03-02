from typing import Any
from pydantic import BaseModel
class PatientResponse(BaseModel):
    id: str
    user_id: str
    date_of_birth: Any = None
    gender: str | None = None
    blood_group: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    insurance_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    created_at: Any = None
    model_config = {"from_attributes": True}
class PatientUpdateRequest(BaseModel):
    date_of_birth: str | None = None
    gender: str | None = None
    blood_group: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    insurance_id: str | None = None
from typing import Any
from pydantic import BaseModel
class DoctorCreateRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str | None = None
    department_id: str
    specialization: str
    registration_number: str
    qualification: str
    experience_years: int = 0
class DoctorResponse(BaseModel):
    id: str
    user_id: str
    department_id: str
    department_name: str | None = None
    specialization: str
    registration_number: str
    qualification: str
    experience_years: int
    status: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    created_at: Any = None
    model_config = {"from_attributes": True}
class DoctorUpdateRequest(BaseModel):
    specialization: str | None = None
    qualification: str | None = None
    experience_years: int | None = None
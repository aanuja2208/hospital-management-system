from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr
class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str
    first_name: str
    last_name: str
    phone: str | None = None
    created_at: Any = None
    doctor_profile: Any = None
    patient_profile: Any = None
    model_config = {"from_attributes": True}
class UserUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
class UserStatusUpdate(BaseModel):
    status: str
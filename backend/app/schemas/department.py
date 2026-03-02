from typing import Any
from pydantic import BaseModel
class DepartmentCreateRequest(BaseModel):
    name: str
    description: str | None = None
class DepartmentResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_active: bool
    doctor_count: int = 0
    created_at: Any = None
    model_config = {"from_attributes": True}
class DepartmentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
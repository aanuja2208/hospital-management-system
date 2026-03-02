from typing import Any
from pydantic import BaseModel
class ScheduleCreateRequest(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str
    slot_duration_minutes: int = 30
    effective_from: str
    effective_until: str | None = None
class ScheduleResponse(BaseModel):
    id: str
    doctor_id: str
    day_of_week: str
    start_time: str
    end_time: str
    slot_duration_minutes: int
    is_active: bool
    effective_from: str
    effective_until: str | None = None
    model_config = {"from_attributes": True}
class ScheduleExceptionCreateRequest(BaseModel):
    exception_date: str
    reason: str
    notes: str | None = None
    is_available: bool = False
    start_time: str | None = None
    end_time: str | None = None
class ScheduleExceptionResponse(BaseModel):
    id: str
    doctor_id: str
    exception_date: str
    reason: str
    notes: str | None = None
    is_available: bool
    model_config = {"from_attributes": True}
class TimeSlotResponse(BaseModel):
    id: str
    doctor_id: str
    slot_date: str
    start_time: str
    end_time: str
    is_booked: bool
    model_config = {"from_attributes": True}
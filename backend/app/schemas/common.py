from uuid import UUID
from pydantic import BaseModel
from typing import Generic, TypeVar
T = TypeVar("T")
class ErrorResponse(BaseModel):
    detail: str
class HealthResponse(BaseModel):
    status: str
    version: str
class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int
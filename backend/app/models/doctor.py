import enum
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.user import gen_uuid
class DoctorStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), ForeignKey("departments.id"), nullable=False)
    specialization: Mapped[str] = mapped_column(String(200), nullable=False)
    registration_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    qualification: Mapped[str] = mapped_column(String(300), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default=DoctorStatus.PENDING.value)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="doctor_profile", lazy="selectin")
    department = relationship("Department", back_populates="doctors", lazy="selectin")
    schedules = relationship("Schedule", back_populates="doctor", lazy="selectin")
    schedule_exceptions = relationship("ScheduleException", back_populates="doctor", lazy="noload")
    appointments = relationship("Appointment", back_populates="doctor", lazy="noload")
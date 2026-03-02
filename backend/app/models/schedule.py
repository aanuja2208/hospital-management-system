import enum
from datetime import time, date, datetime
from sqlalchemy import String, Integer, Boolean, Time, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.user import gen_uuid
class DayOfWeek(str, enum.Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"
class ExceptionReason(str, enum.Enum):
    LEAVE = "LEAVE"
    HOLIDAY = "HOLIDAY"
    EMERGENCY = "EMERGENCY"
class Schedule(Base):
    __tablename__ = "schedules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctor_profiles.id"), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(10), nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_from: Mapped[str] = mapped_column(String(10), nullable=False)
    effective_until: Mapped[str | None] = mapped_column(String(10), nullable=True)
    doctor = relationship("DoctorProfile", back_populates="schedules", lazy="selectin")
    time_slots = relationship("TimeSlot", back_populates="schedule", lazy="noload")
class ScheduleException(Base):
    __tablename__ = "schedule_exceptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctor_profiles.id"), nullable=False)
    exception_date: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=False)
    start_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    doctor = relationship("DoctorProfile", back_populates="schedule_exceptions", lazy="selectin")
class TimeSlot(Base):
    __tablename__ = "time_slots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctor_profiles.id"), nullable=False)
    schedule_id: Mapped[str] = mapped_column(String(36), ForeignKey("schedules.id"), nullable=False)
    slot_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    schedule = relationship("Schedule", back_populates="time_slots", lazy="selectin")
    appointment = relationship("Appointment", back_populates="slot", uselist=False, lazy="selectin")
    __table_args__ = (
        UniqueConstraint("doctor_id", "slot_date", "start_time", name="uq_doctor_slot"),
    )
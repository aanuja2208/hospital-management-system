import enum
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.user import gen_uuid
class AppointmentStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"
VALID_TRANSITIONS = {
    AppointmentStatus.REQUESTED: [AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED],
    AppointmentStatus.CONFIRMED: [AppointmentStatus.CHECKED_IN, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW],
    AppointmentStatus.CHECKED_IN: [AppointmentStatus.IN_PROGRESS],
    AppointmentStatus.IN_PROGRESS: [AppointmentStatus.COMPLETED],
    AppointmentStatus.COMPLETED: [],
    AppointmentStatus.CANCELLED: [],
    AppointmentStatus.NO_SHOW: [],
}
class Appointment(Base):
    __tablename__ = "appointments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patient_profiles.id"), nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctor_profiles.id"), nullable=False)
    slot_id: Mapped[str] = mapped_column(String(36), ForeignKey("time_slots.id"), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AppointmentStatus.REQUESTED.value)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    booked_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    patient = relationship("PatientProfile", back_populates="appointments", lazy="selectin")
    doctor = relationship("DoctorProfile", back_populates="appointments", lazy="selectin")
    slot = relationship("TimeSlot", back_populates="appointment", lazy="selectin")
    encounter = relationship("Encounter", back_populates="appointment", uselist=False, lazy="selectin")
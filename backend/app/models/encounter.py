from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.user import gen_uuid
class Encounter(Base):
    __tablename__ = "encounters"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    appointment_id: Mapped[str] = mapped_column(String(36), ForeignKey("appointments.id"), unique=True, nullable=False)
    doctor_id: Mapped[str] = mapped_column(String(36), ForeignKey("doctor_profiles.id"), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patient_profiles.id"), nullable=False)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    encounter_date: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    appointment = relationship("Appointment", back_populates="encounter", lazy="selectin")
    prescriptions = relationship("Prescription", back_populates="encounter", lazy="selectin")
class Prescription(Base):
    __tablename__ = "prescriptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    encounter_id: Mapped[str] = mapped_column(String(36), ForeignKey("encounters.id"), nullable=False)
    medication_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    encounter = relationship("Encounter", back_populates="prescriptions", lazy="selectin")
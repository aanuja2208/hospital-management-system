from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.encounter import Encounter, Prescription
from app.models.appointment import Appointment
from app.core.exceptions import NotFoundError, BadRequestError
class EncounterService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def create_encounter(self, appointment_id, doctor_id, chief_complaint,
                                diagnosis, clinical_notes, follow_up_instructions, prescriptions):
        result = await self.db.execute(select(Appointment).where(Appointment.id == str(appointment_id)))
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise NotFoundError("Appointment not found")
        if appointment.doctor_id != str(doctor_id):
            raise BadRequestError("Not the assigned doctor")
        result = await self.db.execute(select(Encounter).where(Encounter.appointment_id == str(appointment_id)))
        if result.scalar_one_or_none():
            raise BadRequestError("Encounter already exists")
        encounter = Encounter(
            appointment_id=str(appointment_id), doctor_id=str(doctor_id),
            patient_id=appointment.patient_id,
            chief_complaint=chief_complaint, diagnosis=diagnosis,
            clinical_notes=clinical_notes, follow_up_instructions=follow_up_instructions,
        )
        self.db.add(encounter)
        await self.db.flush()
        for rx in prescriptions:
            p = Prescription(
                encounter_id=encounter.id, medication_name=rx["medication_name"],
                dosage=rx["dosage"], frequency=rx["frequency"],
                duration_days=rx["duration_days"], instructions=rx.get("instructions"),
            )
            self.db.add(p)
        await self.db.flush()
        await self.db.refresh(encounter)
        return encounter
    async def get_encounter(self, encounter_id):
        result = await self.db.execute(select(Encounter).where(Encounter.id == str(encounter_id)))
        enc = result.scalar_one_or_none()
        if not enc:
            raise NotFoundError("Encounter not found")
        return enc
    async def get_patient_history(self, patient_id):
        result = await self.db.execute(
            select(Encounter).where(Encounter.patient_id == str(patient_id))
            .order_by(Encounter.encounter_date.desc())
        )
        return list(result.scalars().all())
    async def add_prescription(self, encounter_id, medication_name, dosage,
                                frequency, duration_days, instructions=None):
        result = await self.db.execute(select(Encounter).where(Encounter.id == str(encounter_id)))
        if not result.scalar_one_or_none():
            raise NotFoundError("Encounter not found")
        p = Prescription(
            encounter_id=str(encounter_id), medication_name=medication_name,
            dosage=dosage, frequency=frequency, duration_days=duration_days,
            instructions=instructions,
        )
        self.db.add(p)
        await self.db.flush()
        return p
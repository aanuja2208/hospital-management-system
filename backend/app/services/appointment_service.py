from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.appointment import Appointment, AppointmentStatus, VALID_TRANSITIONS
from app.models.schedule import TimeSlot
from app.core.exceptions import NotFoundError, BadRequestError, ConflictError, InvalidTransitionError
class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def book(self, patient_id, doctor_id, slot_id, reason=None):
        result = await self.db.execute(select(TimeSlot).where(TimeSlot.id == str(slot_id)))
        slot = result.scalar_one_or_none()
        if not slot:
            raise NotFoundError("Time slot not found")
        if slot.is_booked:
            raise ConflictError("Slot is already booked")
        if slot.doctor_id != str(doctor_id):
            raise BadRequestError("Slot does not belong to the specified doctor")
        slot.is_booked = True
        appointment = Appointment(
            patient_id=str(patient_id), doctor_id=str(doctor_id),
            slot_id=str(slot_id), reason=reason,
            status=AppointmentStatus.REQUESTED.value,
        )
        self.db.add(appointment)
        await self.db.flush()
        await self.db.refresh(appointment)
        return appointment
    async def transition_status(self, appointment_id, new_status, cancel_reason=None):
        result = await self.db.execute(select(Appointment).where(Appointment.id == str(appointment_id)))
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise NotFoundError("Appointment not found")
        current = AppointmentStatus(appointment.status)
        target = new_status if isinstance(new_status, AppointmentStatus) else AppointmentStatus(new_status)
        valid = VALID_TRANSITIONS.get(current, [])
        if target not in valid:
            raise InvalidTransitionError(current.value, target.value)
        now = datetime.now(timezone.utc)
        appointment.status = target.value
        if target == AppointmentStatus.CONFIRMED:
            appointment.confirmed_at = now
        elif target == AppointmentStatus.CHECKED_IN:
            appointment.checked_in_at = now
        elif target == AppointmentStatus.IN_PROGRESS:
            appointment.started_at = now
        elif target == AppointmentStatus.COMPLETED:
            appointment.completed_at = now
        elif target == AppointmentStatus.CANCELLED:
            appointment.cancelled_at = now
            appointment.cancel_reason = cancel_reason
            result = await self.db.execute(select(TimeSlot).where(TimeSlot.id == appointment.slot_id))
            slot = result.scalar_one_or_none()
            if slot:
                slot.is_booked = False
        await self.db.flush()
        return appointment
    async def reschedule(self, appointment_id, new_slot_id):
        result = await self.db.execute(select(Appointment).where(Appointment.id == str(appointment_id)))
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise NotFoundError("Appointment not found")
        if appointment.status in [AppointmentStatus.COMPLETED.value, AppointmentStatus.CANCELLED.value, AppointmentStatus.NO_SHOW.value]:
            raise BadRequestError("Cannot reschedule")
        result = await self.db.execute(select(TimeSlot).where(TimeSlot.id == str(new_slot_id)))
        new_slot = result.scalar_one_or_none()
        if not new_slot:
            raise NotFoundError("New time slot not found")
        if new_slot.is_booked:
            raise ConflictError("New slot is already booked")
        result = await self.db.execute(select(TimeSlot).where(TimeSlot.id == appointment.slot_id))
        old_slot = result.scalar_one_or_none()
        if old_slot:
            old_slot.is_booked = False
        new_slot.is_booked = True
        appointment.slot_id = new_slot.id
        appointment.status = AppointmentStatus.REQUESTED.value
        await self.db.flush()
        return appointment
    async def list_appointments(self, page=1, per_page=20, patient_id=None, doctor_id=None, status=None, **kwargs):
        query = select(Appointment)
        count_query = select(func.count()).select_from(Appointment)
        if patient_id:
            query = query.where(Appointment.patient_id == str(patient_id))
            count_query = count_query.where(Appointment.patient_id == str(patient_id))
        if doctor_id:
            query = query.where(Appointment.doctor_id == str(doctor_id))
            count_query = count_query.where(Appointment.doctor_id == str(doctor_id))
        if status:
            sv = status.value if hasattr(status, 'value') else status
            query = query.where(Appointment.status == sv)
            count_query = count_query.where(Appointment.status == sv)
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * per_page).limit(per_page).order_by(Appointment.booked_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
    async def get_appointment(self, appointment_id):
        result = await self.db.execute(select(Appointment).where(Appointment.id == str(appointment_id)))
        appointment = result.scalar_one_or_none()
        if not appointment:
            raise NotFoundError("Appointment not found")
        return appointment
    async def get_dashboard_stats(self):
        result = await self.db.execute(
            select(Appointment.status, func.count()).group_by(Appointment.status)
        )
        status_counts = {row[0]: row[1] for row in result.all()}
        total_result = await self.db.execute(select(func.count()).select_from(Appointment))
        total = total_result.scalar() or 0
        return {"total": total, "by_status": status_counts}
from datetime import date, timedelta, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.schedule import Schedule, ScheduleException, TimeSlot, DayOfWeek
from app.models.doctor import DoctorProfile
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.user import gen_uuid
DAY_MAPPING = {
    DayOfWeek.MON.value: 0, DayOfWeek.TUE.value: 1, DayOfWeek.WED.value: 2,
    DayOfWeek.THU.value: 3, DayOfWeek.FRI.value: 4, DayOfWeek.SAT.value: 5, DayOfWeek.SUN.value: 6,
}
REVERSE_DAY_MAPPING = {v: k for k, v in DAY_MAPPING.items()}
class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db
    async def create_schedule(self, doctor_id, day_of_week, start_time, end_time,
                              slot_duration_minutes, effective_from, effective_until=None):
        result = await self.db.execute(select(DoctorProfile).where(DoctorProfile.id == doctor_id))
        if not result.scalar_one_or_none():
            raise NotFoundError("Doctor not found")
        schedule = Schedule(
            doctor_id=doctor_id,
            day_of_week=day_of_week if isinstance(day_of_week, str) else day_of_week.value,
            start_time=str(start_time),
            end_time=str(end_time),
            slot_duration_minutes=slot_duration_minutes,
            effective_from=str(effective_from),
            effective_until=str(effective_until) if effective_until else None,
        )
        self.db.add(schedule)
        await self.db.flush()
        return schedule
    async def get_doctor_schedules(self, doctor_id):
        result = await self.db.execute(
            select(Schedule).where(Schedule.doctor_id == doctor_id, Schedule.is_active == True)
        )
        return list(result.scalars().all())
    async def add_exception(self, doctor_id, exception_date, reason, notes=None,
                           is_available=False, start_time=None, end_time=None):
        exc = ScheduleException(
            doctor_id=doctor_id,
            exception_date=str(exception_date),
            reason=reason if isinstance(reason, str) else reason.value,
            notes=notes,
            is_available=is_available,
            start_time=str(start_time) if start_time else None,
            end_time=str(end_time) if end_time else None,
        )
        self.db.add(exc)
        await self.db.flush()
        return exc
    async def generate_slots(self, doctor_id, from_date, to_date):
        schedules = await self.get_doctor_schedules(doctor_id)
        if not schedules:
            return []
        result = await self.db.execute(
            select(ScheduleException).where(
                ScheduleException.doctor_id == doctor_id,
                ScheduleException.exception_date >= str(from_date),
                ScheduleException.exception_date <= str(to_date),
            )
        )
        exceptions = {exc.exception_date: exc for exc in result.scalars().all()}
        result = await self.db.execute(
            select(TimeSlot).where(
                TimeSlot.doctor_id == doctor_id,
                TimeSlot.slot_date >= str(from_date),
                TimeSlot.slot_date <= str(to_date),
            )
        )
        existing_slots = {(s.slot_date, s.start_time) for s in result.scalars().all()}
        new_slots = []
        current = from_date if isinstance(from_date, date) else date.fromisoformat(str(from_date))
        end = to_date if isinstance(to_date, date) else date.fromisoformat(str(to_date))
        while current <= end:
            weekday = current.weekday()
            current_str = current.isoformat()
            if current_str in exceptions and not exceptions[current_str].is_available:
                current += timedelta(days=1)
                continue
            day_enum_val = REVERSE_DAY_MAPPING.get(weekday)
            if not day_enum_val:
                current += timedelta(days=1)
                continue
            for schedule in schedules:
                if schedule.day_of_week != day_enum_val:
                    continue
                eff_from = schedule.effective_from
                if current_str < eff_from:
                    continue
                if schedule.effective_until and current_str > schedule.effective_until:
                    continue
                parts = schedule.start_time.split(':')
                s_hour, s_min = int(parts[0]), int(parts[1])
                parts = schedule.end_time.split(':')
                e_hour, e_min = int(parts[0]), int(parts[1])
                slot_start_mins = s_hour * 60 + s_min
                slot_end_limit = e_hour * 60 + e_min
                dur = schedule.slot_duration_minutes
                while slot_start_mins + dur <= slot_end_limit:
                    sh = slot_start_mins // 60
                    sm = slot_start_mins % 60
                    eh = (slot_start_mins + dur) // 60
                    em = (slot_start_mins + dur) % 60
                    s_time = f"{sh:02d}:{sm:02d}:00"
                    e_time = f"{eh:02d}:{em:02d}:00"
                    if (current_str, s_time) not in existing_slots:
                        slot = TimeSlot(
                            doctor_id=doctor_id,
                            schedule_id=schedule.id,
                            slot_date=current_str,
                            start_time=s_time,
                            end_time=e_time,
                            is_booked=False,
                        )
                        self.db.add(slot)
                        new_slots.append(slot)
                        existing_slots.add((current_str, s_time))
                    slot_start_mins += dur
            current += timedelta(days=1)
        await self.db.flush()
        return new_slots
    async def get_available_slots(self, doctor_id, from_date, to_date):
        await self.generate_slots(doctor_id, from_date, to_date)
        result = await self.db.execute(
            select(TimeSlot).where(
                TimeSlot.doctor_id == doctor_id,
                TimeSlot.slot_date >= str(from_date),
                TimeSlot.slot_date <= str(to_date),
                TimeSlot.is_booked == False,
            ).order_by(TimeSlot.slot_date, TimeSlot.start_time)
        )
        return list(result.scalars().all())
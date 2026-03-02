import asyncio
from datetime import date
from app.database import AsyncSessionLocal, engine, Base
from app.models import *
from app.core.security import hash_password
from app.models.user import gen_uuid
from app.models.schedule import DayOfWeek
async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == "admin@hospital.com"))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return
        admin = User(email="admin@hospital.com", password_hash=hash_password("admin123"),
                     role="ADMIN", status="ACTIVE", first_name="System", last_name="Admin", phone="+1234567890")
        db.add(admin)
        departments = [
            Department(name="Cardiology", description="Heart and cardiovascular system"),
            Department(name="Neurology", description="Brain and nervous system disorders"),
            Department(name="Orthopedics", description="Bones, joints, and muscles"),
            Department(name="Pediatrics", description="Children's healthcare"),
            Department(name="Dermatology", description="Skin conditions and treatments"),
            Department(name="General Medicine", description="Primary and general healthcare"),
            Department(name="Ophthalmology", description="Eye care and vision"),
            Department(name="ENT", description="Ear, nose, and throat conditions"),
        ]
        for d in departments:
            db.add(d)
        await db.flush()
        demo_doctors = [
            {"first": "Sarah", "last": "Johnson", "email": "sarah.johnson@hospital.com", "spec": "Interventional Cardiology", "reg": "DOC-CARD-001", "qual": "MD, DM Cardiology", "exp": 12, "dept": "Cardiology"},
            {"first": "Michael", "last": "Chen", "email": "michael.chen@hospital.com", "spec": "Neurological Surgery", "reg": "DOC-NEUR-001", "qual": "MD, MCh Neurosurgery", "exp": 15, "dept": "Neurology"},
            {"first": "Emily", "last": "Patel", "email": "emily.patel@hospital.com", "spec": "Joint Replacement", "reg": "DOC-ORTH-001", "qual": "MS Orthopedics", "exp": 8, "dept": "Orthopedics"},
            {"first": "James", "last": "Wilson", "email": "james.wilson@hospital.com", "spec": "Pediatric Emergency", "reg": "DOC-PEDI-001", "qual": "MD Pediatrics", "exp": 10, "dept": "Pediatrics"},
            {"first": "Lisa", "last": "Kumar", "email": "lisa.kumar@hospital.com", "spec": "Clinical Dermatology", "reg": "DOC-DERM-001", "qual": "MD Dermatology", "exp": 6, "dept": "Dermatology"},
            {"first": "Robert", "last": "Thompson", "email": "robert.thompson@hospital.com", "spec": "Internal Medicine", "reg": "DOC-GENM-001", "qual": "MD General Medicine", "exp": 20, "dept": "General Medicine"},
        ]
        dept_map = {d.name: d for d in departments}
        for doc in demo_doctors:
            user = User(email=doc["email"], password_hash=hash_password("doctor123"),
                        role="DOCTOR", status="ACTIVE", first_name=doc["first"], last_name=doc["last"])
            db.add(user)
            await db.flush()
            profile = DoctorProfile(user_id=user.id, department_id=dept_map[doc["dept"]].id,
                                    specialization=doc["spec"], registration_number=doc["reg"],
                                    qualification=doc["qual"], experience_years=doc["exp"], status="APPROVED")
            db.add(profile)
            await db.flush()
            for day in ["MON", "TUE", "WED", "THU", "FRI"]:
                schedule = Schedule(doctor_id=profile.id, day_of_week=day,
                                    start_time="09:00:00", end_time="17:00:00",
                                    slot_duration_minutes=30, effective_from=date.today().isoformat(), is_active=True)
                db.add(schedule)
        demo_patients = [
            {"first": "John", "last": "Doe", "email": "john.doe@email.com", "dob": "1990-05-15", "gender": "MALE", "blood": "O+"},
            {"first": "Jane", "last": "Smith", "email": "jane.smith@email.com", "dob": "1985-08-22", "gender": "FEMALE", "blood": "A+"},
            {"first": "Raj", "last": "Patel", "email": "raj.patel@email.com", "dob": "1978-12-03", "gender": "MALE", "blood": "B+"},
        ]
        for pat in demo_patients:
            user = User(email=pat["email"], password_hash=hash_password("patient123"),
                        role="PATIENT", status="ACTIVE", first_name=pat["first"], last_name=pat["last"])
            db.add(user)
            await db.flush()
            profile = PatientProfile(user_id=user.id, date_of_birth=date.fromisoformat(pat["dob"]),
                                     gender=pat["gender"], blood_group=pat["blood"],
                                     address="123 Main St, City", emergency_contact="+1987654321")
            db.add(profile)
        await db.commit()
        print("Database seeded successfully!")
        print("\nDemo Credentials:")
        print("  Admin:   admin@hospital.com / admin123")
        print("  Doctor:  sarah.johnson@hospital.com / doctor123")
        print("  Patient: john.doe@email.com / patient123")
if __name__ == "__main__":
    asyncio.run(seed())
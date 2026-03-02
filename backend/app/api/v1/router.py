from fastapi import APIRouter
from app.api.v1 import auth, admin, departments, schedules, appointments, encounters, users
router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(admin.router)
router.include_router(departments.router)
router.include_router(schedules.router)
router.include_router(appointments.router)
router.include_router(encounters.router)
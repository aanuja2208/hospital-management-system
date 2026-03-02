# Hospital Management Platform

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
# Set up .env (copy from .env and edit if needed)
python seed.py              # Creates tables + demo data
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Demo Credentials
| Role    | Email                        | Password   |
|---------|------------------------------|------------|
| Admin   | admin@hospital.com           | admin123   |
| Doctor  | sarah.johnson@hospital.com   | doctor123  |
| Patient | john.doe@email.com           | patient123 |

### API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Tech Stack
- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL
- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Auth**: JWT (access + refresh tokens) + RBAC

## Project Structure
```
hospital-platform/
├── backend/             # FastAPI REST API
│   ├── app/
│   │   ├── api/v1/      # Route handlers
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── core/        # Security, permissions
│   └── seed.py          # Database seeder
└── frontend/            # React SPA
    └── src/
        ├── components/  # UI components
        ├── features/    # Feature modules
        ├── api/         # API client
        └── contexts/    # Auth context
```

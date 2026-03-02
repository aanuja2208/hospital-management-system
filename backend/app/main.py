from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.api.v1.router import router as v1_router
from app.database import engine, Base
from app.core.exceptions import (
    NotFoundError, BadRequestError, ConflictError,
    UnauthorizedError, ForbiddenError, InvalidTransitionError,
)
settings = get_settings()
BASE_DIR = Path(__file__).parent
HTML_FILE = BASE_DIR / "templates" / "index.html"
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
class SPAMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if (
            response.status_code == 404
            and request.method == "GET"
            and not path.startswith("/api/")
            and not path.startswith("/static/")
            and not path.startswith("/api")
        ):
            return HTMLResponse(content=HTML_FILE.read_text(encoding="utf-8"))
        return response
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Hospital Management Platform — RBAC + Scheduling + Clinical Notes",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SPAMiddleware)
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})
@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})
@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": str(exc)})
@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})
@app.exception_handler(InvalidTransitionError)
async def invalid_transition_handler(request: Request, exc: InvalidTransitionError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(v1_router)
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
@app.get("/", response_class=HTMLResponse)
async def serve_root():
    return HTMLResponse(content=HTML_FILE.read_text(encoding="utf-8"))
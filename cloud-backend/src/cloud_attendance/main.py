import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from cloud_attendance.api import auth, sync, reports, corrections, employees, users
from cloud_attendance.config import DEFAULT_JWT_SECRET, get_settings

logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("cloud_attendance").setLevel(logging.INFO)


def create_app() -> FastAPI:
    _configure_logging()

    if get_settings().jwt_secret == DEFAULT_JWT_SECRET:
        logger.warning(
            "CLOUD_ATTENDANCE_JWT_SECRET is not set; using the default development secret "
            "committed in source control. Tokens signed with it can be forged by anyone who "
            "has read the repository. Set a real secret in .env before real deployment."
        )

    app = FastAPI(
        title="Cloud Attendance API",
        version="0.1.0",
        description=(
            "Cloud dashboard backend for centralizing attendance data and generating reports."
        ),
    )

    # Configure CORS for the cloud-dashboard origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174"],  # common Vite ports
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail and "message" in exc.detail:
            content = exc.detail
        else:
            content = {"error": "http_error", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(sync.router)
    app.include_router(reports.router)
    app.include_router(corrections.router)
    app.include_router(employees.router)
    app.include_router(users.router)
    
    return app


app = create_app()

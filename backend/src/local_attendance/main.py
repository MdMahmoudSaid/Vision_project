import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from local_attendance.api import attendance, auth, dashboard, employees
from local_attendance.config import DEFAULT_JWT_SECRET, get_settings

logger = logging.getLogger(__name__)


class SPAStaticFiles(StaticFiles):
    """Serves the built PWA, falling back to index.html for any path that
    isn't a real static asset. API routes are registered before this mount
    and are matched first, so this only ever runs for client-side routes
    (e.g. /attendance, /search) that have no matching file on disk — without
    the fallback, reloading or deep-linking to any of those routes returns a
    bare 404 instead of the app shell.

    Starlette's own StaticFiles.get_response raises starlette.exceptions.
    HTTPException directly (not fastapi.exceptions.HTTPException, which is a
    subclass and does not match a base-class instance via isinstance/except).
    """

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                return await super().get_response("index.html", scope)
            raise


_LOG_FILE_HANDLER_NAME = "local_attendance_file_handler"


def _configure_logging() -> None:
    """Without any configuration, Python only surfaces WARNING+ (via the
    logging module's built-in "last resort" handler), so the face-detection
    accept/reject diagnostics (confidence, face-size ratio, landmark
    geometry) logged at INFO level in face/deepface_engine.py are otherwise
    invisible in the console — exactly the detail needed to diagnose a
    reported false accept/reject after the fact. basicConfig() is a no-op if
    the root logger already has handlers, so this is safe to call once here.

    Console output alone is lost once the terminal/process is gone, which is
    exactly when a reported false accept/spoof needs investigating after the
    fact — so a rotating file handler persists the same INFO-level
    diagnostics to disk. Guarded by handler name (rather than relying on
    "only called once") since create_app() runs once per test module import
    too, and a second call must not attach a second file handle.
    """
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app_logger = logging.getLogger("local_attendance")
    app_logger.setLevel(logging.INFO)

    if not any(getattr(h, "name", None) == _LOG_FILE_HANDLER_NAME for h in app_logger.handlers):
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler("local_attendance.log", maxBytes=5_000_000, backupCount=3)
        file_handler.name = _LOG_FILE_HANDLER_NAME
        file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        app_logger.addHandler(file_handler)


from contextlib import asynccontextmanager
import asyncio
from local_attendance.sync.scheduler import sync_loop

def create_app() -> FastAPI:
    _configure_logging()

    if get_settings().jwt_secret == DEFAULT_JWT_SECRET:
        logger.warning(
            "LOCAL_ATTENDANCE_JWT_SECRET is not set; using the default development secret "
            "committed in source control. Tokens signed with it can be forged by anyone who "
            "has read the repository. Set a real secret in .env before real deployment."
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        sync_task = asyncio.create_task(sync_loop())
        yield
        # Shutdown
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

    app = FastAPI(
        title="Local Attendance Core API",
        version="0.1.0",
        description=(
            "Local PC API for employee enrollment, facial attendance verification, "
            "duplicate blocking, and shift activity. Cloud dashboard, reports, exports, "
            "and manual corrections are outside this feature."
        ),
        lifespan=lifespan,
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
    app.include_router(attendance.router)
    app.include_router(employees.router)
    app.include_router(dashboard.router)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_root = os.path.dirname(base_dir)
    frontend_dist = os.path.join(project_root, "frontend", "dist")

    if os.path.exists(frontend_dist):
        app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="frontend")
    else:
        logger.warning(f"Frontend dist not found at {frontend_dist}. PWA will not be served.")

    return app


app = create_app()

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from local_attendance.api import attendance, auth, dashboard, employees


def create_app() -> FastAPI:
    app = FastAPI(
        title="Local Attendance Core API",
        version="0.1.0",
        description=(
            "Local PC API for employee enrollment, facial attendance verification, "
            "duplicate blocking, and shift activity. Cloud dashboard, reports, exports, "
            "and manual corrections are outside this feature."
        ),
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

    return app


app = create_app()

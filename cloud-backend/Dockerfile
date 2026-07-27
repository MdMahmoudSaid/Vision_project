# Deploy target: Render/Railway (docs/plan_pointage_facial.md §5) or any
# platform that can run a Dockerfile — the specific host is a deployment-time
# choice, not fixed by this feature. Requires CLOUD_ATTENDANCE_DATABASE_URL to
# point at a real PostgreSQL instance and CLOUD_ATTENDANCE_JWT_SECRET /
# CLOUD_ATTENDANCE_SYNC_API_KEYS to be set via the platform's env config —
# see .env.example.
FROM python:3.11-slim

WORKDIR /app

# WeasyPrint (PDF export) needs Pango/Cairo system libraries — it is not a
# pure-Python wheel dependency.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0 \
    libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install --no-cache-dir .

EXPOSE 8001

# Run migrations, then start the app — a managed platform restarts the
# container on crash, so a failed migration correctly fails the deploy
# rather than serving against a stale schema.
CMD ["sh", "-c", "alembic upgrade head && uvicorn cloud_attendance.main:app --host 0.0.0.0 --port 8001"]

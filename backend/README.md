# Local Attendance Core (Backend)

Local PC service for the facial attendance system: local login, employee
management, facial enrollment, attendance verification, duplicate blocking,
and shift activity. This feature is local-first — it does not require
internet access or a cloud service to record attendance. Cloud sync, reports,
manual corrections, the guard PWA, HTTPS deployment, and NVR/video
integration are out of scope here; see
`specs/001-local-attendance-core/` for the full feature spec.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # adjust values, especially LOCAL_ATTENDANCE_JWT_SECRET
alembic upgrade head
uvicorn local_attendance.main:app --reload
```

The API is served at `http://localhost:8000` and matches
`specs/001-local-attendance-core/contracts/local-api.yaml`.

`opencv-python` and `deepface` are required for real camera capture and face
recognition in production. They are declared in `pyproject.toml` but are not
needed to run the automated test suite (see below).

## Migrations

```bash
alembic upgrade head          # apply all migrations
alembic revision --autogenerate -m "description"   # generate a new migration
```

Migration `001_local_attendance_core` creates the local schema (employees,
local_users, facial_references, verification_attempts, attendance_events,
local_settings). Migration `002_seed_duplicate_window_setting` seeds the
`duplicate_window_seconds` setting with its default of `60`.

## Tests

```bash
pytest
pytest tests/contract
pytest tests/integration
pytest tests/unit
```

Automated tests never touch real hardware. `tests/conftest.py` provides
`fake_camera` and `fake_face_engine` fixtures (implementing the same
`CameraBase` / `FaceEngineBase` interfaces used in production) that are
injected via FastAPI dependency overrides, along with `admin_auth_headers` /
`guard_auth_headers` for RBAC-authenticated requests and an
`employee_with_face` fixture for a ready-to-verify employee. This is also why
`opencv-python` and `deepface` do not need to be installed to run the suite —
the real `OpenCvCamera` and `DeepFaceEngine` adapters are only imported lazily
when the app actually needs a real camera/face engine (see
`camera/base.py:get_camera` and `face/engine.py:get_face_engine`).

## Quickstart validation

The scenarios in `specs/001-local-attendance-core/quickstart.md` are covered
by the automated suite using the fake camera/face engine:

| Scenario | Covered by |
| --- | --- |
| 1. Admin creates employee and enrolls face | `tests/integration/test_face_enrollment.py`, `tests/integration/test_employee_management.py` |
| 2/3. Guard records successful arrival/departure | `tests/integration/test_verified_attendance_success.py` |
| 4. Failed face verification creates no attendance | `tests/integration/test_verified_attendance_failure.py` |
| 5. Duplicate successful submission is blocked | `tests/integration/test_duplicate_blocking.py`, `test_duplicate_attempt_logging.py` |
| 6. Local operation without internet | Inherent: all reads/writes are local SQLite with no outbound calls; no cloud dependency exists in this feature |
| 7. Local role checks | `tests/integration/test_employee_rbac.py`, `tests/integration/test_attendance_edge_cases.py` |

**Manual hardware validation**: Scenarios 1–5 have been run end-to-end
against a real USB/laptop webcam and real DeepFace models (enrollment,
successful/duplicate/failed verification, RBAC). Three real bugs were found
and fixed this way, none of which the fake-hardware test suite could catch:

- `OpenCvCamera` returned black/unusable frames immediately after opening —
  fixed by discarding a few warm-up reads before the real capture
  (`camera/opencv_camera.py`).
- `DeepFaceEngine` relied on DeepFace's default `opencv` (Haar-cascade)
  detector, whose data file is not reliably packaged with `opencv-python` in
  this environment, causing every detection to fail; switched to the
  `retinaface` backend, which DeepFace already depends on
  (`face/deepface_engine.py`).
- `face_match_threshold` defaulted to `0.4`, but the code compares plain
  (unnormalized) Euclidean ArcFace distances, whose correct DeepFace-tuned
  same-person threshold is `4.15` — fixed in `config.py` and `.env.example`.

Still worth re-checking on the actual client PC/camera before go-live:
enrollment/verification latency under 5 seconds, and face-match accuracy at
the configured `LOCAL_ATTENDANCE_FACE_MATCH_THRESHOLD` under that site's
lighting conditions.

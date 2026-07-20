# Implementation Plan: Local Attendance Core

**Branch**: `001-local-attendance-core` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-local-attendance-core/spec.md`

## Summary

Build the local PC attendance core that lets a guard or local administrator
authenticate locally, manage employee identity records, enroll facial references
from the fixed USB camera, verify arrival/departure attendance, log every
verification attempt, persist confirmed attendance events locally, and prevent
duplicate successful submissions inside the configured window. This feature is
local-first: internet and cloud dashboard availability are not required for
recording raw attendance.

Technical approach: a Python local web service exposes the guard-facing API,
persists local data in SQLite, captures frames from the fixed USB webcam,
calculates/stores face embeddings, compares verification captures against the
selected employee's reference, and writes all events with sync markers for later
cloud features.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic, Pydantic
v2, passlib/bcrypt, python-jose or PyJWT, OpenCV, DeepFace, NumPy

**Storage**: SQLite on the local PC for employees, users, facial references,
verification attempts, attendance events, and local configuration

**Testing**: pytest, FastAPI TestClient/httpx, pytest fixtures for SQLite test
databases, mocked camera adapter, mocked face engine for deterministic tests

**Target Platform**: Local PC at the guard post, reachable by the guard PWA on
the same local Wi-Fi network

**Project Type**: Local web service/API with hardware integration

**Performance Goals**: Guard sees a success/failure result within 5 seconds for
the primary attendance flow under realistic local conditions; employee
enrollment completes in under 1 minute when the camera view is suitable

**Constraints**: Must work without internet; raw attendance data is local-first;
must not store or replay video; must not expose face embeddings to clients; must
log failed attempts without creating attendance events; must enforce local
roles server-side; duplicate window defaults to 60 seconds

**Scale/Scope**: One guard post, one local PC, one USB webcam, local Admin and
Guard roles, local attendance core only. Guard PWA, cloud dashboard, manual
corrections, reports, exports, and site deployment hardening are later features.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Local Attendance Truth and Offline Reliability**: PASS. The design keeps
  raw attendance records and verification attempts in local SQLite and does not
  require cloud availability for the guard workflow.
- **II. Verified Presence and Complete Auditability**: PASS. Attendance events
  are created only from successful verification attempts; failed attempts are
  recorded separately.
- **III. Backend-Enforced RBAC and Data Protection**: PASS. Local roles are
  enforced by backend dependencies/middleware, and facial references are never
  returned to guard-facing clients.
- **IV. Guard-First Simplicity and Contract-First UI**: PASS. The API contract
  supports the simple guard flow and stable mock-driven UI work.
- **V. Incremental SDD and Testable Delivery**: PASS. This feature is an
  independently testable local attendance slice with contracts, data model, and
  quickstart validation.

No constitution violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-local-attendance-core/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── local-api.yaml
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   └── local_attendance/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── employees.py
│       │   ├── attendance.py
│       │   └── dashboard.py
│       ├── auth/
│       │   ├── dependencies.py
│       │   ├── password.py
│       │   └── tokens.py
│       ├── camera/
│       │   ├── base.py
│       │   └── opencv_camera.py
│       ├── face/
│       │   ├── engine.py
│       │   └── deepface_engine.py
│       ├── models/
│       │   ├── employee.py
│       │   ├── user.py
│       │   ├── facial_reference.py
│       │   ├── verification_attempt.py
│       │   ├── attendance_event.py
│       │   └── setting.py
│       ├── schemas/
│       │   ├── auth.py
│       │   ├── employee.py
│       │   ├── attendance.py
│       │   └── dashboard.py
│       └── services/
│           ├── employee_service.py
│           ├── face_enrollment_service.py
│           ├── verification_service.py
│           ├── attendance_service.py
│           └── settings_service.py
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

**Structure Decision**: Use the repository's planned `backend/` directory for
the local PC service. The guard PWA in `frontend/` remains a later feature and
will consume `contracts/local-api.yaml`.

## Phase 0: Research

Research output is captured in [research.md](./research.md). All technical
unknowns for this feature are resolved there. Remaining project-wide Phase 0
items from the constitution that are not required to implement this feature
(cloud hosting, printed report layout, cloud corrections direction) are deferred
to later feature plans.

## Phase 1: Design and Contracts

Design outputs:

- [data-model.md](./data-model.md)
- [contracts/local-api.yaml](./contracts/local-api.yaml)
- [quickstart.md](./quickstart.md)

### Post-Design Constitution Check

- **Local-first recording**: PASS. Data model stores all raw local records with
  sync status but does not depend on cloud availability.
- **Auditability**: PASS. Verification attempts and attendance events are
  separate entities, and attendance events reference the successful attempt.
- **RBAC/data protection**: PASS. Contracts require bearer authentication and do
  not expose facial reference vectors.
- **Guard simplicity**: PASS. Contracts support select employee, choose type,
  verify, and review recent activity.
- **Testable delivery**: PASS. Quickstart contains independent validation
  scenarios for enrollment, successful attendance, failed verification,
  duplicate blocking, local outage operation, and role checks.

## Complexity Tracking

No constitution violations or extra architecture complexity require tracking.

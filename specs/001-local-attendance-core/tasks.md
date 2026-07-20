# Tasks: Local Attendance Core

**Input**: Design documents from `/specs/001-local-attendance-core/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/local-api.yaml, quickstart.md

**Tests**: Included because the project constitution requires focused validation for RBAC, auditability, duplicate blocking, failed verification behavior, and local-first persistence.

**Organization**: Tasks are grouped by user story so Claude Code can implement and validate each increment independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the backend project skeleton, dependency setup, application entrypoint, and test harness.

- [X] T001 Create backend Python package structure from plan.md in backend/src/local_attendance/ and backend/tests/
- [X] T002 Create backend/pyproject.toml with FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, auth, OpenCV, DeepFace, NumPy, pytest, httpx, and dev dependencies
- [X] T003 Create backend/src/local_attendance/config.py with local settings for database URL, JWT secret, token expiry, camera index, duplicate window default, and face threshold
- [X] T004 Create backend/src/local_attendance/main.py with FastAPI app factory, router registration placeholders, health route, and OpenAPI metadata matching specs/001-local-attendance-core/contracts/local-api.yaml
- [X] T005 Create backend/src/local_attendance/database.py with SQLAlchemy engine/session setup and dependency helpers for SQLite
- [X] T006 Create backend/alembic.ini and backend/alembic/env.py wired to backend/src/local_attendance/database.py metadata
- [X] T007 [P] Create backend/tests/conftest.py with isolated SQLite test database, FastAPI TestClient fixture, and dependency override helpers
- [X] T008 [P] Create backend/tests/unit/test_config.py covering duplicate window default and required local settings

**Checkpoint**: Backend imports, test harness starts, and the app can expose a health route without feature endpoints.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared models, migrations, auth, RBAC, camera/face interfaces, and common response schemas before user story work begins.

**CRITICAL**: No user story work should begin until this phase is complete.

- [X] T009 Create SQLAlchemy base metadata and timestamp mixins in backend/src/local_attendance/models/__init__.py
- [X] T010 [P] Create Employee model in backend/src/local_attendance/models/employee.py with fields from data-model.md and unique employee_number constraint
- [X] T011 [P] Create Local User model in backend/src/local_attendance/models/user.py with username uniqueness, password_hash, role enum, and active flag
- [X] T012 [P] Create Facial Reference model in backend/src/local_attendance/models/facial_reference.py with employee relationship, serialized embedding, sample_count, quality_status, created_by_user_id, and replaced_at
- [X] T013 [P] Create Verification Attempt model in backend/src/local_attendance/models/verification_attempt.py with result enum, failure_reason, similarity_score, synced flag, and optional attendance_event_id
- [X] T014 [P] Create Attendance Event model in backend/src/local_attendance/models/attendance_event.py with type enum, source auto, synced flag, and verification_attempt_id relationship
- [X] T015 [P] Create Local Setting model in backend/src/local_attendance/models/setting.py with unique key and value fields
- [X] T016 Create initial Alembic migration in backend/alembic/versions/001_local_attendance_core.py for all local core tables and constraints
- [X] T017 Create Pydantic schemas for auth requests/responses in backend/src/local_attendance/schemas/auth.py matching LoginRequest, LoginResponse, and LocalUser
- [X] T018 Create Pydantic schemas for employees and face enrollment in backend/src/local_attendance/schemas/employee.py matching EmployeeCreate, EmployeeUpdate, EmployeeSummary, EmployeeDetail, FaceEnrollmentRequest, and FaceEnrollmentResponse
- [X] T019 Create Pydantic schemas for attendance in backend/src/local_attendance/schemas/attendance.py matching AttendanceVerifyRequest, VerificationAttempt, AttendanceEvent, and AttendanceVerifyResponse
- [X] T020 Create Pydantic schemas for dashboard overview and shift activity in backend/src/local_attendance/schemas/dashboard.py matching ShiftActivityItem and LocalOverview
- [X] T021 Create password hashing helpers in backend/src/local_attendance/auth/password.py using bcrypt-compatible hashing and verification
- [X] T022 Create JWT token helpers in backend/src/local_attendance/auth/tokens.py with subject, role, expiry, and validation errors
- [X] T023 Create auth dependencies in backend/src/local_attendance/auth/dependencies.py for current user, admin-required, and guard-or-admin-required access
- [X] T024 Create auth router in backend/src/local_attendance/api/auth.py implementing POST /auth/login with inactive-user and bad-password handling
- [X] T025 [P] Create camera base interface in backend/src/local_attendance/camera/base.py for single-frame capture and capture errors
- [X] T026 [P] Create OpenCV camera adapter in backend/src/local_attendance/camera/opencv_camera.py without storing raw video frames
- [X] T027 [P] Create face engine interface in backend/src/local_attendance/face/engine.py for enroll(samples) and compare(capture, reference) results
- [X] T028 [P] Create DeepFace adapter skeleton in backend/src/local_attendance/face/deepface_engine.py behind the face engine interface
- [X] T029 Create settings service in backend/src/local_attendance/services/settings_service.py to read duplicate_window_seconds with 60 second default
- [X] T030 [P] Create unit tests for auth password and token helpers in backend/tests/unit/test_auth_helpers.py
- [X] T031 [P] Create unit tests for camera and face engine interfaces using fakes in backend/tests/unit/test_hardware_interfaces.py
- [X] T032 Create integration test for Alembic migration and model relationships in backend/tests/integration/test_database_schema.py

**Checkpoint**: Database schema, auth/RBAC, schemas, and hardware abstraction are ready for independently testable user stories.

---

## Phase 3: User Story 1 - Record Verified Attendance (Priority: P1) MVP

**Goal**: Guard selects an active employee, chooses arrival or departure, and records attendance only after successful face verification; every attempt is logged.

**Independent Test**: With one admin-created employee and fake face reference, verify successful arrival, successful departure, failed verification, and offline local persistence without any cloud service.

### Tests for User Story 1

- [X] T033 [P] [US1] Create contract tests for POST /auth/login and POST /attendance/verify responses in backend/tests/contract/test_attendance_verify_contract.py
- [X] T034 [P] [US1] Create integration tests for successful arrival and departure creating linked verification attempts and attendance events in backend/tests/integration/test_verified_attendance_success.py
- [X] T035 [P] [US1] Create integration tests for failed verification creating a failed attempt and zero attendance events in backend/tests/integration/test_verified_attendance_failure.py
- [X] T036 [P] [US1] Create integration tests for unauthorized, inactive employee, missing face reference, and unusable camera capture cases in backend/tests/integration/test_attendance_edge_cases.py

### Implementation for User Story 1

- [X] T037 [US1] Implement attendance service orchestration in backend/src/local_attendance/services/attendance_service.py for successful event creation from a successful verification attempt
- [X] T038 [US1] Implement verification service in backend/src/local_attendance/services/verification_service.py to load employee reference, capture camera frame, compare face, and return success/failure decisions
- [X] T039 [US1] Implement verification attempt persistence in backend/src/local_attendance/services/verification_service.py for all authorized verification outcomes
- [X] T040 [US1] Implement POST /attendance/verify endpoint in backend/src/local_attendance/api/attendance.py with guard-or-admin RBAC and AttendanceVerifyResponse schema
- [X] T041 [US1] Wire attendance router into backend/src/local_attendance/main.py
- [X] T042 [US1] Ensure failed verification, unusable capture, inactive employee, and missing reference return clear ErrorResponse or failed AttendanceVerifyResponse without creating attendance events in backend/src/local_attendance/api/attendance.py
- [X] T043 [US1] Add local persistence behavior for synced=false on verification attempts and attendance events in backend/src/local_attendance/services/attendance_service.py

**Checkpoint**: User Story 1 works independently and proves the MVP: verified local attendance with complete attempt logging.

---

## Phase 4: User Story 2 - Register Employee Facial Reference (Priority: P2)

**Goal**: Admin creates/updates employee profiles and enrolls or re-enrolls usable facial references from the fixed camera.

**Independent Test**: Create employee, verify generated employee number, enroll face with accepted samples, re-enroll face without deleting attendance history, and reject unusable captures.

### Tests for User Story 2

- [X] T044 [P] [US2] Create contract tests for GET /employees, POST /employees, PATCH /employees/{employee_id}, and POST /employees/{employee_id}/face in backend/tests/contract/test_employee_contract.py
- [X] T045 [P] [US2] Create integration tests for employee create/update/search and employee_number auto-generation in backend/tests/integration/test_employee_management.py
- [X] T046 [P] [US2] Create integration tests for face enrollment, face re-enrollment, and rejected unusable captures in backend/tests/integration/test_face_enrollment.py
- [X] T047 [P] [US2] Create RBAC tests proving guard cannot create employees or enroll faces and admin can in backend/tests/integration/test_employee_rbac.py

### Implementation for User Story 2

- [X] T048 [US2] Implement employee service in backend/src/local_attendance/services/employee_service.py for create, update, search, active filtering, and generated unique employee numbers
- [X] T049 [US2] Implement face enrollment service in backend/src/local_attendance/services/face_enrollment_service.py for multi-sample capture, face engine enrollment, usable/rejected outcomes, and replacement of prior active references
- [X] T050 [US2] Implement employees router in backend/src/local_attendance/api/employees.py for GET /employees, POST /employees, PATCH /employees/{employee_id}, and POST /employees/{employee_id}/face
- [X] T051 [US2] Wire employees router into backend/src/local_attendance/main.py
- [X] T052 [US2] Ensure employee and face endpoints never return serialized embeddings or password-like secrets in backend/src/local_attendance/schemas/employee.py
- [X] T053 [US2] Add service-level validation for blank full_name, duplicate employee_number, inactive employee updates, and missing employee records in backend/src/local_attendance/services/employee_service.py

**Checkpoint**: User Story 2 can register and prepare employees for the MVP attendance flow without exposing biometric data.

---

## Phase 5: User Story 3 - Prevent Duplicate Submissions (Priority: P3)

**Goal**: Reject repeated successful attendance submissions for the same employee and attendance type inside the configured duplicate window.

**Independent Test**: Submit the same employee/type twice inside 60 seconds and confirm only one attendance event exists, then submit after the window and confirm normal evaluation.

### Tests for User Story 3

- [X] T054 [P] [US3] Create integration tests for duplicate arrival and departure blocking inside the configured window in backend/tests/integration/test_duplicate_blocking.py
- [X] T055 [P] [US3] Create unit tests for duplicate window setting fallback and custom setting parsing in backend/tests/unit/test_settings_service.py
- [X] T056 [P] [US3] Create integration test proving duplicate_blocked creates a verification attempt but no attendance event in backend/tests/integration/test_duplicate_attempt_logging.py

### Implementation for User Story 3

- [X] T057 [US3] Implement duplicate event lookup in backend/src/local_attendance/services/attendance_service.py for same employee, same type, and configured time window
- [X] T058 [US3] Update verification workflow in backend/src/local_attendance/services/verification_service.py to return duplicate_blocked after successful face verification when duplicate check fails
- [X] T059 [US3] Update POST /attendance/verify response handling in backend/src/local_attendance/api/attendance.py to return duplicate_blocked with a guard-friendly message
- [X] T060 [US3] Seed duplicate_window_seconds default value through migration or startup initialization in backend/src/local_attendance/services/settings_service.py

**Checkpoint**: Duplicate protection is enforced server-side and cannot be bypassed by repeated client calls.

---

## Phase 6: User Story 4 - Review Local Shift Activity (Priority: P4)

**Goal**: Guard or admin reviews recent local attendance activity, with successful events and failed attempts clearly separated.

**Independent Test**: Generate one success, one failure, and one duplicate-blocked attempt, then confirm the activity response identifies each outcome correctly.

### Tests for User Story 4

- [X] T061 [P] [US4] Create contract tests for GET /attendance/shift-activity and GET /dashboard/overview in backend/tests/contract/test_shift_activity_contract.py
- [X] T062 [P] [US4] Create integration tests for shift activity ordering, limit parameter, and outcome labeling in backend/tests/integration/test_shift_activity.py
- [X] T063 [P] [US4] Create integration tests for local overview counts for arrivals, departures, and failed attempts in backend/tests/integration/test_local_overview.py

### Implementation for User Story 4

- [X] T064 [US4] Implement shift activity query in backend/src/local_attendance/services/attendance_service.py combining recent attendance events and failed or duplicate-blocked verification attempts
- [X] T065 [US4] Implement GET /attendance/shift-activity in backend/src/local_attendance/api/attendance.py with guard-or-admin RBAC and limit validation
- [X] T066 [US4] Implement local overview service logic in backend/src/local_attendance/services/attendance_service.py for today arrival, departure, and failed attempt counts
- [X] T067 [US4] Implement GET /dashboard/overview in backend/src/local_attendance/api/dashboard.py and wire dashboard router into backend/src/local_attendance/main.py

**Checkpoint**: Local operators can see recent activity and distinguish attendance from failed verification attempts.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, contract alignment, quickstart validation, security pass, and readiness for Claude Code handoff completion.

- [X] T068 [P] Update backend README or docs with local development setup, migration command, test command, and fake camera/face test mode in backend/README.md
- [X] T069 [P] Verify implemented responses match specs/001-local-attendance-core/contracts/local-api.yaml and update the contract only if implementation reveals a necessary compatible correction
- [X] T070 [P] Add .env.example for backend local settings in backend/.env.example without secrets
- [X] T071 Run quickstart scenarios from specs/001-local-attendance-core/quickstart.md and document any manual hardware limitations in backend/README.md
- [X] T072 Run full backend test suite with pytest from backend/ and fix failures in the touched backend files
- [X] T073 Review security constraints in .specify/memory/constitution.md against implemented auth, RBAC, and biometric data exposure paths in backend/src/local_attendance/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP first.
- **User Story 2 (Phase 4)**: Depends on Foundational; can be developed alongside US1 after shared models/services exist, but validates best after US1.
- **User Story 3 (Phase 5)**: Depends on US1 attendance creation flow.
- **User Story 4 (Phase 6)**: Depends on US1 attempt/event persistence and benefits from US3 outcomes.
- **Polish (Phase 7)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 Record Verified Attendance**: Requires foundational auth, models, camera interface, face interface, and database.
- **US2 Register Employee Facial Reference**: Requires foundational auth, employee model, facial reference model, camera interface, and face interface.
- **US3 Prevent Duplicate Submissions**: Requires US1 attendance creation and settings service.
- **US4 Review Local Shift Activity**: Requires US1 verification attempts and attendance events; includes duplicate outcomes if US3 is complete.

### Within Each User Story

- Tests are listed before implementation and should be written first when practical.
- Models and schemas precede services.
- Services precede API endpoints.
- API endpoints are complete only after RBAC and response schemas are wired.
- Each checkpoint should pass before moving to the next dependent phase.

## Parallel Opportunities

- Setup tasks T007 and T008 can run in parallel with package skeleton work after T001.
- Foundational model tasks T010 through T015 can run in parallel.
- Foundational interface tasks T025 through T028 can run in parallel.
- Contract and integration test tasks inside each user story can run in parallel because they target separate test files.
- US1 and US2 can partially proceed in parallel after Phase 2 because they mostly touch different services and routers, but integration should validate employee enrollment before real attendance verification.

## Parallel Example: User Story 1

```bash
Task: "T033 [US1] Create contract tests for POST /auth/login and POST /attendance/verify responses in backend/tests/contract/test_attendance_verify_contract.py"
Task: "T034 [US1] Create integration tests for successful arrival and departure creating linked verification attempts and attendance events in backend/tests/integration/test_verified_attendance_success.py"
Task: "T035 [US1] Create integration tests for failed verification creating a failed attempt and zero attendance events in backend/tests/integration/test_verified_attendance_failure.py"
Task: "T036 [US1] Create integration tests for unauthorized, inactive employee, missing face reference, and unusable camera capture cases in backend/tests/integration/test_attendance_edge_cases.py"
```

## Parallel Example: User Story 2

```bash
Task: "T044 [US2] Create contract tests for GET /employees, POST /employees, PATCH /employees/{employee_id}, and POST /employees/{employee_id}/face in backend/tests/contract/test_employee_contract.py"
Task: "T045 [US2] Create integration tests for employee create/update/search and employee_number auto-generation in backend/tests/integration/test_employee_management.py"
Task: "T046 [US2] Create integration tests for face enrollment, face re-enrollment, and rejected unusable captures in backend/tests/integration/test_face_enrollment.py"
Task: "T047 [US2] Create RBAC tests proving guard cannot create employees or enroll faces and admin can in backend/tests/integration/test_employee_rbac.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 Setup.
2. Complete Phase 2 Foundational.
3. Complete Phase 3 US1.
4. Stop and validate successful attendance, failed verification, local persistence, and RBAC for `/attendance/verify`.

### Incremental Delivery

1. Add US2 so real employees and facial references can be managed.
2. Add US3 duplicate protection once attendance creation exists.
3. Add US4 local activity and overview for operational visibility.
4. Finish Phase 7 polish and quickstart validation.

### Claude Code Handoff

Claude Code should start from T001 and proceed in task order. If implementation reveals a contract mismatch, update the implementation to match `contracts/local-api.yaml` unless the contract is clearly impossible; only then make a minimal compatible contract correction and mention it in the handoff notes.

## Notes

- Keep all raw attendance writes local-first with `synced=false`.
- Do not implement cloud sync, manual corrections, reports, exports, frontend PWA screens, HTTPS deployment, or NVR/video integration in this feature.
- Do not expose facial embeddings or raw captured images in API responses.
- Use fake camera and fake face engine in automated tests; real camera validation belongs to quickstart/manual testing.

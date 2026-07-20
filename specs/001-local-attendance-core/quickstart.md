# Quickstart: Local Attendance Core

This guide validates the feature end to end once implementation tasks are
complete. It is intentionally a validation guide, not implementation code.

## Prerequisites

- Local PC has the fixed USB camera connected and aimed at the attendance
  position.
- Backend dependencies are installed.
- Local database migrations have run.
- A local admin account and a local guard account exist.
- Camera and face engine can be swapped for deterministic mocks during tests.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn local_attendance.main:app --reload
```

Expected outcome: local API starts and exposes the contract described in
`specs/001-local-attendance-core/contracts/local-api.yaml`.

## Scenario 1: Admin creates employee and enrolls face

1. Log in as local admin.
2. Create an employee with `full_name`; omit `employee_number` to validate
   automatic generation.
3. Enroll the employee face using the fixed camera.

Expected outcomes:

- Employee is active and has a unique employee number.
- Facial reference status is usable.
- Face embedding or reference data is not returned to the client.
- The flow can complete in under 1 minute when the camera view is suitable.

## Scenario 2: Guard records successful arrival

1. Log in as local guard.
2. Search/select the enrolled employee.
3. Choose `arrival`.
4. Trigger verification with the employee physically present.

Expected outcomes:

- Result is `success`.
- One verification attempt is recorded.
- One attendance event is recorded and linked to that attempt.
- Result is visible to the caller in under 5 seconds.

## Scenario 3: Guard records successful departure

1. Use the same enrolled employee.
2. Choose `departure`.
3. Trigger verification with the employee physically present.

Expected outcomes:

- Result is `success`.
- One departure event is recorded and linked to its verification attempt.
- Arrival and departure are separate attendance events.

## Scenario 4: Failed face verification creates no attendance

1. Select an enrolled employee.
2. Trigger verification with a different person or an unusable face capture.

Expected outcomes:

- Result is `failed`.
- A failed verification attempt is recorded with a failure reason.
- No attendance event is created.
- Shift activity shows the failed attempt as failed verification, not as
  attendance.

## Scenario 5: Duplicate successful submission is blocked

1. Record a successful arrival for an employee.
2. Within 60 seconds, submit another successful arrival for the same employee.

Expected outcomes:

- Result is `duplicate_blocked`.
- No second attendance event is created.
- The response explains that recent attendance was already recorded.

## Scenario 6: Local operation without internet

1. Disable internet while keeping local network access to the PC.
2. Record a successful attendance event.
3. Review local shift activity.

Expected outcomes:

- Attendance recording succeeds locally.
- Verification attempt and attendance event remain visible locally.
- Records are marked for later synchronization.

## Scenario 7: Local role checks

1. Log in as guard and attempt to create an employee.
2. Log in as guard and attempt to enroll a face.
3. Log in as admin and perform the same actions.

Expected outcomes:

- Guard is denied employee management and face enrollment.
- Admin is allowed to create employees and enroll faces.
- Backend denial occurs even if the client attempts the request directly.

## Test Commands

```bash
cd backend
pytest
pytest tests/contract
pytest tests/integration
```

Expected outcome: tests cover contract responses, enrollment success/failure,
attendance success/failure, duplicate blocking, local storage persistence, and
role-based access checks.

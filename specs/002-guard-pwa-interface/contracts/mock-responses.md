# Mock Responses: Guard PWA Local Interface

These are example payloads for every screen state this feature needs, shaped
exactly per `specs/001-local-attendance-core/contracts/local-api.yaml`. They
let frontend implementation (and MSW-based tests) start immediately without a
running backend, per the constitution's "Frontend work ... MUST start from
stable API contracts, mock responses, and acceptance scenarios" principle.
These are illustrative fixtures, not new contract schemas — the authoritative
schemas remain in Feature 001's `local-api.yaml`.

## POST /auth/login

**Success (200)**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { "id": "8c3e7b99-1a01-4a3a-a2a4-ef38f64040b2", "username": "guard1", "role": "guard" }
}
```

**Invalid credentials (401)**

```json
{ "error": "invalid_credentials", "message": "Invalid credentials or inactive account" }
```

## GET /employees?query=&active=true

**Results found (200)**

```json
[
  {
    "id": "10937fd3-7eac-4ec4-b517-141b5004d8bd",
    "full_name": "Amina Haddad",
    "employee_number": "EMP0001",
    "department": "Warehouse",
    "active": true,
    "has_face_reference": true
  }
]
```

**No matches (200, empty array)** — the UI must show a clear "no matches"
state, not an empty screen.

```json
[]
```

## POST /employees (admin only)

**Created (201)**

```json
{
  "id": "a9786b9a-250b-445d-841c-dfe01ff67336",
  "full_name": "New Employee",
  "employee_number": "EMP0002",
  "department": null,
  "active": true,
  "has_face_reference": false,
  "job_title": null,
  "phone": null,
  "notes": null,
  "registration_date": "2026-07-20",
  "created_at": "2026-07-20T12:23:26.401Z",
  "updated_at": "2026-07-20T12:23:26.401Z"
}
```

**Guard attempts this action (403)** — should not be reachable from the UI at
all for a guard, but the client must still handle it defensively.

```json
{ "error": "forbidden", "message": "Admin role required" }
```

## POST /employees/{employee_id}/face (admin only)

**Enrolled (200)**

```json
{
  "employee_id": "a9786b9a-250b-445d-841c-dfe01ff67336",
  "status": "usable",
  "sample_count": 8,
  "enrolled_at": "2026-07-20T14:35:10.009Z"
}
```

**Capture unusable (400)** — must be shown in plain language, not as a
technical camera/model error.

```json
{ "error": "capture_unusable", "message": "No usable face could be produced from the capture" }
```

## POST /attendance/verify

**Success (200)**

```json
{
  "result": "success",
  "message": "Attendance recorded",
  "verification_attempt": {
    "id": "62cad2fe-28e0-4179-aeb5-b9a40cd2848c",
    "employee_id": "a9786b9a-250b-445d-841c-dfe01ff67336",
    "guard_id": "8c3e7b99-1a01-4a3a-a2a4-ef38f64040b2",
    "type_requested": "arrival",
    "timestamp": "2026-07-20T14:39:38.502Z",
    "result": "success",
    "similarity_score": 1.3,
    "failure_reason": null,
    "attendance_event_id": "b1c2d3e4-1111-2222-3333-444455556666"
  },
  "attendance_event": {
    "id": "b1c2d3e4-1111-2222-3333-444455556666",
    "employee_id": "a9786b9a-250b-445d-841c-dfe01ff67336",
    "guard_id": "8c3e7b99-1a01-4a3a-a2a4-ef38f64040b2",
    "type": "arrival",
    "timestamp": "2026-07-20T14:39:38.502Z",
    "verification_attempt_id": "62cad2fe-28e0-4179-aeb5-b9a40cd2848c",
    "source": "auto"
  }
}
```

**Failed — face mismatch (200)** — a real outcome, not an HTTP error; the UI
must render this as a clear failure, distinct from duplicate-blocked.

```json
{
  "result": "failed",
  "message": "Face verification failed",
  "verification_attempt": {
    "id": "72cad2fe-28e0-4179-aeb5-b9a40cd2848c",
    "employee_id": "a9786b9a-250b-445d-841c-dfe01ff67336",
    "guard_id": "8c3e7b99-1a01-4a3a-a2a4-ef38f64040b2",
    "type_requested": "arrival",
    "timestamp": "2026-07-20T14:41:00.000Z",
    "result": "failed",
    "similarity_score": 3.9,
    "failure_reason": "face_mismatch",
    "attendance_event_id": null
  },
  "attendance_event": null
}
```

**Duplicate blocked (200)**

```json
{
  "result": "duplicate_blocked",
  "message": "Recent attendance was already recorded for this employee",
  "verification_attempt": {
    "id": "82cad2fe-28e0-4179-aeb5-b9a40cd2848c",
    "employee_id": "a9786b9a-250b-445d-841c-dfe01ff67336",
    "guard_id": "8c3e7b99-1a01-4a3a-a2a4-ef38f64040b2",
    "type_requested": "arrival",
    "timestamp": "2026-07-20T14:39:50.000Z",
    "result": "duplicate_blocked",
    "similarity_score": 1.1,
    "failure_reason": "duplicate_recent_attendance",
    "attendance_event_id": null
  },
  "attendance_event": null
}
```

**Employee inactive / missing reference / capture unusable / employee not
found (400)** — all rendered the same way in the UI: a plain-language error
banner, none of them implying attendance was recorded.

```json
{ "error": "employee_inactive", "message": "Employee is not active" }
```

```json
{ "error": "missing_reference", "message": "Employee has no usable facial reference" }
```

## GET /attendance/shift-activity?limit=50

```json
[
  {
    "kind": "attendance_event",
    "employee_id": "a9786b9a-250b-445d-841c-dfe01ff67336",
    "employee_name": "Amina Haddad",
    "type": "arrival",
    "timestamp": "2026-07-20T14:39:38.502Z",
    "guard_username": "guard1",
    "outcome": "success",
    "failure_reason": null,
    "attendance_event_id": "b1c2d3e4-1111-2222-3333-444455556666"
  },
  {
    "kind": "verification_attempt",
    "employee_id": "a9786b9a-250b-445d-841c-dfe01ff67336",
    "employee_name": "Amina Haddad",
    "type": "arrival",
    "timestamp": "2026-07-20T14:41:00.000Z",
    "guard_username": "guard1",
    "outcome": "failed",
    "failure_reason": "face_mismatch",
    "attendance_event_id": null
  }
]
```

## GET /dashboard/overview

```json
{ "date": "2026-07-20", "arrivals": 4, "departures": 3, "failed_attempts": 1 }
```

## Client-only state: connection error

Not part of `local-api.yaml` — shown when a `fetch` call to the local API
fails entirely (network error, timeout, DNS failure on the local Wi-Fi). The
UI must render this distinctly from a `400`/`401`/`403` response, since no
server-side decision was made at all.

```json
{ "outcome": "connection_error", "message": "Can't reach the local system. Check the Wi-Fi connection." }
```

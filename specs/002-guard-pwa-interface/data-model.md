# Data Model: Guard PWA Local Interface

These are client-side view models only. There is no database in this
feature; every field is either received from or sent to Feature 001's local
API (`specs/001-local-attendance-core/contracts/local-api.yaml`), whose
schemas remain the source of truth. Nothing here is persisted beyond the
current browser session/page state.

## Guard Session

Represents the logged-in state used to decide what the UI shows and when to
force re-login.

**Fields**

- `token`: the bearer token returned by `POST /auth/login`, held in
  memory/`sessionStorage` only
- `userId`, `username`, `role` (`admin` | `guard`): from the `LocalUser`
  object in `LoginResponse`

**Validation Rules**

- Never persisted to `localStorage` or any durable client storage.
- Cleared immediately on logout or when any API call returns 401.
- `role` drives which navigation items and pages are shown (FR-011), but the
  actual authorization decision always happens server-side (FR-012) — this
  field must never be treated as a security boundary in the UI code.

**State Transitions**

- `anonymous` → `authenticated` after a successful `POST /auth/login`
- `authenticated` → `anonymous` on logout or any 401 response from the API

## Employee Search Result

A lightweight, display-only projection of an active employee, used for
selection before verification or management actions.

**Fields**

- `id`, `fullName`, `employeeNumber`, `department` (optional), `active`,
  `hasFaceReference` — mirrors `EmployeeSummary` from the contract

**Validation Rules**

- Only entries with `active: true` are offered for attendance selection
  (FR-004); inactive employees may still appear in an admin's management
  list but are visually marked and not selectable for verification.
- Never includes facial embedding or any biometric data — the contract's
  `EmployeeSummary`/`EmployeeDetail` schemas already exclude it, and the UI
  must not request or display it even if a future contract change added it.

## Attendance Verification Outcome

The plain-language result shown after triggering verification.

**Fields**

- `outcome`: `success` | `failed` | `duplicate_blocked` | `connection_error`
  (`connection_error` is a client-only state for when the API cannot be
  reached at all — not part of the contract's `result` enum)
- `message`: guard-friendly text, either passed through from the API
  response's `message` field or, for `connection_error`, a client-owned
  message
- `employeeName`, `type` (`arrival` | `departure`), `timestamp`: for display
  on the result screen

**Validation Rules**

- `success` is the only outcome that implies an attendance event was
  recorded; the UI must never imply a recording happened for any other
  outcome (FR-007).
- `duplicate_blocked` must be visually and textually distinct from `failed`
  (FR-007) — it means the employee's attendance was already recorded
  recently, not that verification itself failed.

## Shift Activity Item

A single row in the recent-activity list, mirrored from
`ShiftActivityItem` in the contract.

**Fields**

- `kind`: `attendance_event` | `verification_attempt`
- `employeeName`, `type` (optional), `timestamp`, `guardUsername` (optional)
- `outcome`: `success` | `failed` | `duplicate_blocked`
- `failureReason` (optional)

**Validation Rules**

- Items with `outcome !== "success"` must be visually distinguished from
  successful attendance events (FR-010) — they represent attempts, not
  confirmed attendance.

## Notes on form-only state (not formal entities)

Employee creation (`EmployeeCreate`) and face enrollment
(`FaceEnrollmentRequest`/`FaceEnrollmentResponse`) use the contract's request
schemas directly as form state for the admin-only screens (US4); they are not
duplicated here as separate entities since they map 1:1 onto
`specs/001-local-attendance-core/contracts/local-api.yaml` with no
additional client-side fields beyond ordinary form-validation state (for
example, "submitting" / "error" flags local to the form component).

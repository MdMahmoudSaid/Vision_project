# Data Model: Cloud Dashboard, Sync, and Reports

Two schemas are affected: a small addition to the existing local PC schema
(`backend/`, SQLite, Feature 001), and a new cloud schema
(`cloud-backend/`, PostgreSQL in production / SQLite in tests). Field names
below use the same conventions already established by
`backend/src/local_attendance/models` (UUID `String(36)` primary keys via
`generate_uuid()`, `Enum(..., native_enum=False)`, `DateTime(timezone=True)`,
a shared `TimestampMixin` for `created_at`/`updated_at`).

## Local PC schema change (`backend/`)

### `Employee` (existing table — one column added)

| Field | Type | Notes |
|---|---|---|
| `synced` | `bool`, default `False` | **New.** Mirrors the existing `VerificationAttempt.synced` / `AttendanceEvent.synced` pattern. Set to `False` on create and on every update; the sync job flips it to `True` after the cloud confirms the employee record was received. |

No other local tables change. `VerificationAttempt.synced` and
`AttendanceEvent.synced` already exist (added in Feature 001 in
anticipation of this feature) and need no schema change — only a consumer
(the sync job) that was missing until now.

### New local table: `sync_runs` (optional operational log, local only)

| Field | Type | Notes |
|---|---|---|
| `id` | `String(36)`, PK | `generate_uuid()` |
| `started_at` | `DateTime(timezone=True)` | |
| `finished_at` | `DateTime(timezone=True)`, nullable | Null while a run is in progress. |
| `employees_pushed` | `int`, default 0 | Count synced this run. |
| `attendance_events_pushed` | `int`, default 0 | |
| `verification_attempts_pushed` | `int`, default 0 | |
| `status` | `Enum(success, partial_failure, failed)` | `partial_failure` when some records synced and others failed within the same run. |
| `error_message` | `Text`, nullable | Last error encountered, for on-site troubleshooting. |

Purely diagnostic — never read by the cloud or exposed to guards; helps an
admin see "is sync actually working" without opening logs.

## Cloud schema (`cloud-backend/`, new)

### `synced_employees`

Cloud-side mirror of the local `Employee`, keyed by the **same UUID** the
local PC generated (see research.md §3).

| Field | Type | Notes |
|---|---|---|
| `id` | `String(36)`, PK | Same value as the local `Employee.id` — never generated cloud-side. |
| `full_name` | `String(255)` | |
| `employee_number` | `String(64)`, unique | |
| `department` | `String(255)`, nullable | |
| `job_title` | `String(255)`, nullable | |
| `active` | `bool` | |
| `has_face_reference` | `bool` | Derived flag only — never the embedding itself (spec Assumptions: biometric data never leaves the local PC). |
| `registration_date` | `Date` | |
| `synced_at` | `DateTime(timezone=True)` | When the cloud last received an update for this employee. |

### `synced_verification_attempts`

| Field | Type | Notes |
|---|---|---|
| `id` | `String(36)`, PK | Same value as local `VerificationAttempt.id`. |
| `employee_id` | `String(36)`, FK → `synced_employees.id` | |
| `type_requested` | `Enum(arrival, departure)` | |
| `timestamp` | `DateTime(timezone=True)` | |
| `result` | `Enum(success, failed, duplicate_blocked)` | |
| `similarity_score` | `float`, nullable | |
| `failure_reason` | `String(255)`, nullable | |
| `attendance_event_id` | `String(36)`, nullable | Denormalized pointer, same convention as the local model. |
| `synced_at` | `DateTime(timezone=True)` | |

### `synced_attendance_events`

| Field | Type | Notes |
|---|---|---|
| `id` | `String(36)`, PK | Same value as local `AttendanceEvent.id`. |
| `employee_id` | `String(36)`, FK → `synced_employees.id` | |
| `type` | `Enum(arrival, departure)` | |
| `timestamp` | `DateTime(timezone=True)` | |
| `verification_attempt_id` | `String(36)`, FK → `synced_verification_attempts.id` | |
| `synced_at` | `DateTime(timezone=True)` | |

`synced_employees`/`synced_attendance_events`/`synced_verification_attempts`
are written only by the sync ingestion endpoint (never by a cloud dashboard
user directly) — this is what makes conflict resolution unnecessary (spec
Assumptions, research.md §3).

### `corrections`

| Field | Type | Notes |
|---|---|---|
| `id` | `String(36)`, PK | `generate_uuid()`, cloud-generated (this table has no local counterpart — FR-022). |
| `employee_id` | `String(36)`, FK → `synced_employees.id` | |
| `attendance_event_id` | `String(36)`, nullable, FK → `synced_attendance_events.id` | Null when adding a missing arrival/departure rather than editing an existing event. |
| `action` | `Enum(add_arrival, add_departure, correct_time, change_type)` | Per `docs/plan_pointage_facial.md` §6. |
| `previous_value` | `Text` (JSON) | Null for `add_arrival`/`add_departure` (nothing existed before). |
| `new_value` | `Text` (JSON) | The corrected timestamp/type, or the newly added event's data. |
| `reason` | `Text`, not null, non-empty | Required per spec FR-008/009/010. |
| `performed_by` | `String(36)`, FK → `cloud_users.id` | |
| `performed_at` | `DateTime(timezone=True)` | |

Append-only: no `UPDATE`/`DELETE` route ever exists for this table (spec
FR-010, US3 acceptance scenario 4). A second correction to the same event is
simply a new row referencing the same `attendance_event_id`.

**Validation rules**:
- `reason` MUST be non-empty (enforced at the Pydantic schema layer before
  the service layer ever constructs a `Correction`).
- `action IN (correct_time, change_type)` MUST reference an existing
  `attendance_event_id`; `action IN (add_arrival, add_departure)` MUST NOT
  (the event doesn't exist yet — the correction *is* the record of it).

### `cloud_users`

| Field | Type | Notes |
|---|---|---|
| `id` | `String(36)`, PK | `generate_uuid()` |
| `email` | `String(255)`, unique | Login identifier. |
| `password_hash` | `String(255)` | bcrypt, same scheme as `local_users.password_hash`. |
| `role` | `Enum(owner, admin, viewer)` | **Guard intentionally excluded** — per the resolved spec clarification (FR-023), Guard accounts never get a `cloud_users` row; the cloud backend still recognizes the string `"guard"` in a decoded JWT solely to reject it (defense in depth, in case a local guard/admin JWT is ever mistakenly presented to the cloud API). |
| `active` | `bool`, default `True` | Revocation sets this to `False`; `get_current_cloud_user` rejects inactive users the same way `local_attendance`'s equivalent dependency already does. |
| `invited_by` | `String(36)`, nullable, FK → `cloud_users.id` | Which Owner invited this user; null for the first bootstrap Owner account. |

**State transitions**: `active: True → False` (revoke) is the only
transition; there is no "reactivate" flow in this feature (an Owner can
always invite a fresh account if needed) — reactivation can be added later
without a breaking schema change if the client asks for it.

### `sync_ingest_log` (operational, cloud-side)

| Field | Type | Notes |
|---|---|---|
| `id` | `String(36)`, PK | |
| `received_at` | `DateTime(timezone=True)` | |
| `employees_count` / `attendance_events_count` / `verification_attempts_count` | `int` | Counts accepted in that batch (including already-existing IDs treated as successful no-ops). |
| `site_key_id` | `String(36)` | Which sync credential made the call (see research.md §6) — supports multi-site in the future without a schema change, even though V1 has one site. |

## Report view model (computed, not a stored table)

A `Report` is generated at request time from `synced_attendance_events` (+
any applicable `corrections`, which override the raw synced value for
display) — it is never persisted as its own table. Its shape:

| Field | Meaning |
|---|---|
| `scope` | `{ type: "employee", employee_id }` or `{ type: "organization" }` |
| `period` | `{ granularity: "day"\|"week"\|"month"\|"custom", date_from, date_to }` |
| `rows` | One per employee-day: `employee_id`, `employee_name`, `date`, `arrival_time` (nullable), `departure_time` (nullable), `worked_duration` (nullable — null when incomplete), `completeness` (`complete`\|`missing_departure`\|`missing_arrival`\|`no_record`), `corrected` (bool — true if any correction touched this employee-day) |
| `generated_at` | Timestamp shown on the export (FR-014). |
| `may_be_incomplete` | `bool` — true if the requested period extends past the most recent successful sync (FR-017). |

## Entity relationship summary

```text
cloud_users (Owner/Admin/Viewer only)
   └─writes→ corrections
                 └─references→ synced_attendance_events (nullable)
                 └─references→ synced_employees

synced_employees ←sync-writes-only← [local PC sync job]
   └─has many→ synced_attendance_events
                   └─references→ synced_verification_attempts
   └─has many→ synced_verification_attempts

sync_ingest_log — operational audit of each sync batch received
```

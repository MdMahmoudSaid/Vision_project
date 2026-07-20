# Data Model: Local Attendance Core

## Employee

Represents a person whose attendance can be verified locally.

**Fields**

- `id`: unique local identifier
- `full_name`: required display name
- `employee_number`: required unique employee number, generated if not supplied
- `department`: optional department
- `job_title`: optional job title
- `phone`: optional phone number
- `notes`: optional administrative notes
- `registration_date`: date the employee was registered locally
- `active`: whether the employee can be selected for attendance
- `created_at`: creation timestamp
- `updated_at`: last update timestamp

**Relationships**

- Has zero or one active Facial Reference
- Has many Verification Attempts
- Has many Attendance Events through successful attempts

**Validation Rules**

- `full_name` must not be blank.
- `employee_number` must be unique among local employees.
- Inactive employees cannot be used for new attendance verification.

**State Transitions**

- `draft/no_face` -> `active_with_face` after successful face enrollment
- `active_with_face` -> `active_with_face` after re-enrollment
- `active_with_face` -> `inactive` when disabled by an authorized user

## Local User

Represents a local account used by an administrator or guard.

**Fields**

- `id`: unique local identifier
- `username`: required unique login name
- `password_hash`: hashed password
- `role`: `admin` or `guard`
- `active`: whether the account can authenticate
- `created_at`: creation timestamp
- `updated_at`: last update timestamp

**Validation Rules**

- Passwords are never stored in plain text.
- Inactive users cannot authenticate.
- Guard users cannot manage employees or facial references unless explicitly
  allowed by a later feature.

## Facial Reference

Represents the local biometric reference used to verify one employee.

**Fields**

- `id`: unique local identifier
- `employee_id`: referenced employee
- `embedding`: serialized face embedding or embedding aggregate
- `sample_count`: number of accepted enrollment samples used
- `quality_status`: `usable` or `rejected`
- `created_by_user_id`: local user who enrolled the reference
- `created_at`: creation timestamp
- `replaced_at`: timestamp if superseded by re-enrollment

**Relationships**

- Belongs to one Employee
- Created by one Local User

**Validation Rules**

- A usable reference requires at least one accepted face sample.
- A new usable reference replaces the previous active reference without deleting
  attendance history.
- Embeddings are sensitive and must not be returned in API responses.

**State Transitions**

- `capture_started` -> `usable` after accepted sample processing
- `capture_started` -> `rejected` when no usable face can be produced
- `usable` -> `replaced` after successful re-enrollment

## Verification Attempt

Represents every attempt to verify a selected employee for an arrival or
departure, whether successful or failed.

**Fields**

- `id`: unique local identifier
- `employee_id`: selected employee
- `guard_id`: local user who triggered verification
- `type_requested`: `arrival` or `departure`
- `timestamp`: time of the attempt
- `result`: `success`, `failed`, or `duplicate_blocked`
- `similarity_score`: comparison score when available
- `failure_reason`: reason for failure when applicable
- `attendance_event_id`: linked attendance event when success creates one
- `synced`: false until later cloud sync confirms upload
- `created_at`: creation timestamp

**Relationships**

- Belongs to one Employee
- Belongs to one Local User acting as guard
- Has zero or one Attendance Event

**Validation Rules**

- Every verification request must create a Verification Attempt unless the user
  is unauthenticated or unauthorized.
- Failed attempts must not create Attendance Events.
- `attendance_event_id` is present only when an Attendance Event exists.

## Attendance Event

Represents a confirmed arrival or departure.

**Fields**

- `id`: unique local identifier
- `employee_id`: verified employee
- `type`: `arrival` or `departure`
- `timestamp`: confirmed attendance time
- `guard_id`: guard who triggered verification
- `verification_attempt_id`: successful attempt that produced this event
- `source`: `auto`
- `synced`: false until later cloud sync confirms upload
- `created_at`: creation timestamp

**Relationships**

- Belongs to one Employee
- Belongs to one Local User acting as guard
- Belongs to one successful Verification Attempt

**Validation Rules**

- Must be created only from a successful Verification Attempt.
- Must not be created for failed verification, unusable capture, inactive
  employee, unauthorized user, or duplicate-blocked request.
- Duplicate prevention checks existing Attendance Events for same employee and
  same type inside the configured window.

## Local Setting

Stores local configuration values needed by this feature.

**Fields**

- `key`: unique setting key
- `value`: setting value
- `updated_at`: last update timestamp

**Required Setting**

- `duplicate_window_seconds`: defaults to `60`

## Derived Views

### Local Shift Activity

Read model combining recent Attendance Events and Verification Attempts.

**Fields**

- `kind`: `attendance_event` or `verification_attempt`
- `employee_id`
- `employee_name`
- `type_requested` or `type`
- `timestamp`
- `guard_username`
- `outcome`
- `failure_reason`
- `attendance_event_id`

# Feature Specification: Cloud Dashboard, Sync, and Reports

**Feature Branch**: `003-cloud-dashboard-sync-reports`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Feature 003: dashboard cloud, sync et rapports. Couvre Phase 4 : backend cloud, PostgreSQL, RBAC Owner/Admin/Guard/Viewer, sync local vers cloud, rapports jour/semaine/mois/période, PDF, Excel, dashboard UI. (Grounded in docs/plan_pointage_facial.md, Phase 4, §6, §7, §16, §20.)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Synced Attendance Data in the Cloud (Priority: P1)

An Owner or Admin logs into the cloud dashboard from any internet-connected
device and sees the employees, attendance events, and verification attempts
that were recorded on the local PC, without needing to be on the local Wi-Fi
network. When the local PC has internet access, newly recorded events appear
in the cloud within a bounded, predictable delay. When the local PC has no
internet access for a period, nothing is lost: once connectivity returns, all
pending events sync up without duplication or gaps. The local PC keeps
writing raw attendance data locally exactly as before (Feature 001); this
feature only adds the one-way push to the cloud.

**Why this priority**: Without reliable sync, there is no cloud dashboard to
build anything else on top of. This is the foundation every other story in
this feature depends on.

**Independent Test**: Can be tested by recording attendance events on the
local PC (some while "offline", simulated by disconnecting internet), then
restoring connectivity and confirming every event appears exactly once in the
cloud dashboard with matching employee, type, timestamp, and verification
outcome.

**Acceptance Scenarios**:

1. **Given** the local PC has internet access, **When** a guard records a
   successful arrival or departure, **Then** the event appears in the cloud
   dashboard within the defined sync delay, with the same employee, type,
   timestamp, and verifying guard as recorded locally.
2. **Given** the local PC loses internet access for an extended period while
   continuing to serve guards normally, **When** connectivity is restored,
   **Then** every attendance event and verification attempt recorded while
   offline is synced to the cloud exactly once, with no duplicates and no
   missing records.
3. **Given** the sync process is interrupted mid-batch (e.g., connection drops
   partway through), **When** the local PC retries, **Then** the cloud state
   ends up identical to a completed sync, with no duplicate or partial
   records.
4. **Given** an employee's profile or facial-enrollment status changes on the
   local PC, **When** the change syncs, **Then** the cloud dashboard reflects
   the updated employee metadata (not the biometric data itself).

---

### User Story 2 - Generate and Export Attendance Reports (Priority: P2)

An Owner, Admin, or Viewer opens the reports area of the cloud dashboard and
requests a daily, weekly, monthly, or custom-period report. Daily, weekly,
and monthly reports cover every employee for that period (an organization-wide
view, matching the guard-post's day-to-day oversight need). A custom-period
report can additionally be scoped to a single employee for a full history
lookup. Every report shows each employee's arrivals, departures, and any
incomplete pairs (e.g., an arrival with no matching departure), and can be
exported as PDF, exported as Excel, or printed directly, carrying the
company name, employee name/number, the period covered, the arrival/departure
table, a note of any missing records, the report generation date, and a
signature area, per the client's required report format.

**Why this priority**: Reporting is the primary reason the client wants a
cloud dashboard at all — it is the deliverable that gets compared against
payroll and the client's separate NVR footage. It depends on synced data
existing (Story 1) but does not depend on corrections or user management.

**Independent Test**: Can be tested by generating a report for a known set of
synced attendance events and confirming the on-screen report, the PDF export,
and the Excel export all show matching, correct entries and required fields.

**Acceptance Scenarios**:

1. **Given** synced attendance data for all employees on a given day, **When**
   the user requests the daily report for that date, **Then** the report
   lists every employee's arrival/departure for that day, flagging any
   employee with an incomplete pair.
2. **Given** synced attendance data for an employee over a custom range,
   **When** the user requests a custom-period report scoped to that employee,
   **Then** the report shows every arrival/departure in that range for that
   employee only.
3. **Given** a generated report, **When** the user exports to PDF, **Then**
   the downloaded file contains the same data shown on screen, formatted for
   printing with company name, employee name/number, period, the
   arrival/departure table, missing-record notes, generation date, and a
   signature area.
4. **Given** a generated report, **When** the user exports to Excel, **Then**
   the downloaded spreadsheet contains the same data shown on screen, with one
   row per attendance event or per employee-day, suitable for further
   analysis.
5. **Given** a Viewer account, **When** they generate and export a report,
   **Then** the export succeeds but no data-modifying action is available to
   them anywhere in the flow.
6. **Given** a report is requested for a period that includes data the local
   PC has not yet synced, **When** the report is generated, **Then** it
   visibly indicates it may be incomplete as of the current sync state.

---

### User Story 3 - Correct Missing or Wrong Attendance Records (Priority: P3)

An Admin or Owner reviewing the dashboard notices a gap (e.g., a guard forgot
to trigger a departure verification, or the local NVR shows the employee left
at a different time than what was recorded). They open the employee's history
and add a manual correction: a missing arrival, a missing departure, a
corrected timestamp, or a swapped arrival/departure type. A reason is
required. The system keeps the original record intact, and records who made
the change, when, the previous value, and the new value in an audit trail.

**Why this priority**: Valuable for data accuracy and dispute resolution, but
the dashboard and reports already deliver value without it, and it depends on
Story 1's synced data existing to have something to correct. This is a
required V1 capability per the project's cahier de charge and constitution,
not an optional add-on.

**Independent Test**: Can be tested by creating a correction against a synced
event, confirming the original event is still visible and unchanged, the
correction appears with reason/author/timestamp, and reports reflect the
corrected value while the audit trail still shows the original.

**Acceptance Scenarios**:

1. **Given** an employee is missing a departure event for a shift, **When** an
   Owner or Admin adds a missing-departure correction with a reason, **Then**
   a new attendance record is created, marked as manually corrected, linked to
   the author, the change timestamp, and the stated reason.
2. **Given** an existing attendance event has an incorrect timestamp or
   arrival/departure type, **When** an Owner or Admin corrects it with a
   reason, **Then** the original event remains stored and visible in the
   audit trail, and the corrected value is what reports and the dashboard use
   going forward.
3. **Given** a Viewer account, **When** they view an employee's history,
   **Then** they cannot see any control to add or edit a correction.
4. **Given** an Owner or Admin opens the audit trail for an employee, **Then**
   they see every correction ever made, in order, with old value, new value,
   reason, author, and timestamp — none of which can be deleted or edited
   after the fact.
5. **Given** a correction is created on the cloud dashboard, **When** the
   local PC's own records are checked, **Then** the local PC's original
   record is unaffected — corrections live only in the cloud, which is the
   system of record for reports and audit going forward.

---

### User Story 4 - Enforce Roles Across the Cloud Dashboard (Priority: P4)

An Owner manages who has cloud dashboard access and at what role: Owner,
Admin, or Viewer. The Guard role exists in the project's shared permission
matrix and authentication-token scheme, but Guard accounts are managed
locally (Features 001/002) and never receive cloud dashboard access — the
cloud backend still recognizes the Guard role value solely to reject it. The
Owner can invite a new cloud user, assign or change a role, and revoke
access. Every cloud endpoint checks the caller's role before allowing the
action, regardless of what the dashboard UI shows or hides.

**Why this priority**: Necessary for onboarding real staff beyond the initial
account and for closing off unauthorized access, but the dashboard, reports,
and corrections already deliver value to a single Owner/Admin before
multi-user management is a blocker.

**Independent Test**: Can be tested by having an Owner invite a new Admin,
confirming the new Admin can log in and perform Admin-scoped actions, then
having the Owner revoke that Admin's access and confirming they can no longer
log in. Also testable by attempting a correction or user-management call
directly against the backend with a Viewer or Guard token and confirming it
is rejected.

**Acceptance Scenarios**:

1. **Given** an Owner is logged in, **When** they invite a new cloud user with
   a chosen role (Owner, Admin, or Viewer), **Then** that user can set up
   access and log in with exactly the permissions of the assigned role.
2. **Given** an Owner changes an existing user's role, **When** that user next
   acts in the dashboard, **Then** their available actions reflect the new
   role immediately.
3. **Given** an Owner revokes a user's access, **When** that user attempts to
   log in or continues an existing session, **Then** access is denied.
4. **Given** an Admin, Guard, or Viewer account, **When** they look for
   user-management controls, **Then** none are available to them, and any
   direct backend request to manage users is rejected regardless of role.
5. **Given** a request reaches the cloud backend with any role, **When** that
   role does not include the requested action per the permission matrix,
   **Then** the backend rejects the request — the UI hiding a control is
   never the only protection.

---

### Edge Cases

- What happens when the same attendance event is synced twice due to a retry
  (e.g., the local PC sent it, the cloud saved it, but the local PC never
  received the confirmation and retries)? The cloud MUST recognize it as the
  same event and MUST NOT create a duplicate.
- What happens when the local PC has been offline for a very long time (days)
  and accumulates a large backlog? Sync MUST eventually catch up completely
  without requiring manual intervention or losing records, even if it takes
  multiple sync cycles.
- What happens when an employee is deleted (including force-deleted with
  history, per the local system's existing admin capability) on the local PC
  after some of their records already synced to the cloud? The cloud MUST
  have a defined, consistent behavior (retain the synced history for
  audit/reporting purposes) rather than silently erroring or losing data.
- What happens when two corrections are made to the same attendance event
  over time? The audit trail MUST preserve the full chain of changes, not
  just the most recent correction.
- What happens when a report is requested for a date range that includes data
  not yet synced from the local PC? The report MUST clearly indicate that it
  may be incomplete as of the current sync state, rather than silently
  presenting partial data as final.
- What happens when a Viewer or Guard tries to reach a correction or
  user-management URL directly (not through the UI)? The system MUST deny the
  action server-side regardless of how the request was made.
- What happens if the cloud backend is temporarily unavailable? The local PC
  and guard PWA MUST continue operating normally (per Feature 001's
  constitution guarantee); sync simply resumes when the cloud is reachable
  again.
- What happens to a correction that references an attendance event that was
  itself created by an earlier correction? The audit trail MUST still show
  the full chain back to the original (or the original absence of a record),
  not just the immediately preceding value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST sync attendance events, verification attempts,
  and employee/facial-reference metadata (not raw biometric templates) from
  the local PC to the cloud backend whenever the local PC has internet
  connectivity.
- **FR-002**: Sync MUST be idempotent: re-sending or retrying a sync of the
  same locally-recorded record MUST NOT create duplicate records in the
  cloud.
- **FR-003**: Sync MUST resume cleanly after any connectivity gap, eventually
  delivering every locally-recorded record to the cloud without manual
  intervention.
- **FR-004**: The cloud backend MUST NOT be required for the local guard
  workflow (login, employee search, arrival/departure verification) to keep
  functioning; local operation remains fully independent of cloud
  availability.
- **FR-005**: The cloud dashboard MUST support authenticated access under the
  same four-role permission matrix as the local system: Owner, Admin, Guard,
  and Viewer, with roles carried in the authentication token and checked by
  the backend on every protected endpoint.
- **FR-006**: Owners and Admins MUST be able to browse the synced list of
  employees and view each employee's attendance history, date by date, in the
  cloud dashboard.
- **FR-007**: Viewers MUST be able to browse employees, view attendance
  history, generate reports, and export/print reports, but MUST NOT be able
  to create, edit, or delete any data (employees, corrections, users).
- **FR-008**: Owners and Admins MUST be able to create a manual correction
  that adds a missing arrival or departure event, with a required reason.
- **FR-009**: Owners and Admins MUST be able to create a manual correction
  that changes the timestamp or arrival/departure type of an existing
  attendance event, with a required reason.
- **FR-010**: Every correction MUST preserve the original record unchanged,
  and MUST record the author, the timestamp of the change, the previous
  value, and the new value.
- **FR-011**: Owners and Admins MUST be able to view a complete, ordered,
  read-only audit trail of every correction made to an employee's attendance
  history.
- **FR-012**: The reporting module MUST support daily, weekly, and monthly
  organization-wide reports (all employees for the period), and a custom
  date-range report optionally scoped to a single employee.
- **FR-013**: Reports MUST reflect corrected values where corrections exist,
  while the audit trail continues to expose the original values separately.
- **FR-014**: Users MUST be able to export any generated report as a PDF
  file, and the PDF MUST include the company name, employee name/number (or
  "all employees" for organization-wide reports), the period covered, the
  arrival/departure table, a note of any missing records, the report
  generation date, and a signature area.
- **FR-015**: Users MUST be able to export any generated report as an Excel
  spreadsheet file.
- **FR-016**: Users MUST be able to print a generated report directly from
  the dashboard in the same print-friendly layout as the PDF export.
- **FR-017**: A report covering a date range with attendance data not yet
  synced from the local PC MUST indicate to the user that it may be
  incomplete.
- **FR-018**: All cloud-side authorization decisions (role checks for
  corrections, user management, and data access) MUST be enforced by the
  cloud backend, not only hidden in the dashboard UI.
- **FR-019**: The system MUST NOT implement video storage, video playback,
  NVR/RTSP integration, or a dispute-review video player as part of this
  feature.
- **FR-020**: Owners MUST be able to invite new cloud users, assign each a
  role (Owner, Admin, or Viewer), change an existing user's role, and revoke
  a user's access.
- **FR-021**: A user whose cloud access has been revoked MUST be denied
  further access, including denial of any already-active session on their
  next action.
- **FR-022**: Corrections created on the cloud dashboard MUST NOT modify or
  require any write-back to the local PC's own records; the local PC remains
  the unmodified source of truth for raw locally-recorded events, and the
  cloud becomes the system of record for corrected/reported values.
- **FR-023**: The cloud dashboard MUST be exclusively for Owner, Admin, and
  Viewer accounts. A Guard-role token MUST be recognized by the cloud
  backend solely so that it can be correctly rejected from every
  dashboard-only endpoint; Guard accounts have no cloud dashboard login or
  UI, and continue to use only the local PC/PWA (Features 001/002) for their
  entire workflow, including viewing their own shift activity.

### Key Entities

- **Synced Employee Record**: The cloud-side copy of an employee's
  non-biometric profile (name, employee number, department, active status,
  whether they have a usable facial reference), kept up to date from the
  local PC via sync; the cloud never receives or stores the raw facial
  embedding.
- **Synced Attendance Event**: The cloud-side copy of a local attendance
  event (employee, type, timestamp, recording guard, linked verification
  attempt), uniquely identified so repeated syncs cannot duplicate it.
- **Synced Verification Attempt**: The cloud-side copy of a local
  verification attempt (employee, requested type, result, failure reason if
  any, timestamp), used for audit and troubleshooting rather than for
  computing worked hours.
- **Sync Cursor/State**: Tracks how much of the local PC's data has already
  been delivered to the cloud, so sync can resume correctly after a gap
  without re-sending everything or skipping anything.
- **Correction**: A cloud-created record describing a manual add or edit to
  attendance data — links to the affected employee (and original event, if
  editing one), the author, timestamp, reason, previous value, and new value.
  Corrections are append-only; none are ever edited or deleted after
  creation. Corrections exist only in the cloud (see FR-022).
- **Report**: A generated view of attendance data for a chosen period
  (day/week/month/custom range), optionally scoped to one employee,
  combining synced events with any applicable corrections, and the basis for
  the on-screen view plus PDF/Excel/print outputs.
- **Cloud User Account**: An Owner, Admin, or Viewer identity with cloud-side
  authentication, a role, and an active/revoked status. Guard accounts are
  local-only (Features 001/002) and have no corresponding cloud user account.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When the local PC has internet access, a newly recorded
  attendance event is visible in the cloud dashboard within 5 minutes at
  least 95% of the time.
- **SC-002**: After a local PC connectivity gap of any length, 100% of
  attendance events and verification attempts recorded during that gap are
  present in the cloud exactly once (no duplicates, no losses) once
  connectivity is restored and sync completes.
- **SC-003**: An Owner, Admin, or Viewer can generate a daily/weekly/monthly
  organization-wide report or a custom per-employee report and receive an
  on-screen result in under 5 seconds for a single-employee custom report and
  under 15 seconds for a monthly organization-wide report, under realistic
  data volumes.
- **SC-004**: 100% of generated reports export to PDF and Excel with data
  that matches the on-screen report exactly, and every PDF export contains
  all client-required fields (company name, employee identification, period,
  arrival/departure table, missing-record notes, generation date, signature
  area).
- **SC-005**: 100% of corrections made are traceable in the audit trail with
  author, reason, timestamp, previous value, and new value, and the original
  record remains independently retrievable.
- **SC-006**: 0% of Viewer-role or Guard-role sessions can successfully
  perform a data-modifying action (correction, user management, employee
  edit) on the cloud dashboard, whether attempted through the UI or directly
  against the backend.
- **SC-007**: Local guard attendance operations continue to succeed with 0%
  dependency on cloud backend availability, verified by exercising the full
  guard flow while the cloud backend is intentionally unreachable.
- **SC-008**: An Owner can revoke a user's cloud access, and that user is
  denied access on their next action in under 1 minute of the revocation.

## Assumptions

- The local PC (Feature 001) and its API are the only source of attendance
  and verification data; the cloud never accepts attendance-event writes
  directly from guards or from any client other than the sync process itself
  and explicit Owner/Admin corrections.
- The cloud backend is reachable over the general internet (not only the
  local Wi-Fi network) and is hosted independently of the local PC's uptime;
  the specific hosting provider and budget are an implementation/deployment
  decision made during planning, not a user-facing requirement.
- Employee facial embeddings are never transmitted to or stored in the cloud;
  only non-biometric employee metadata syncs.
- Report totals (worked duration, completeness) are computed by pairing
  arrival and departure events per employee per day; unmatched pairs are
  flagged rather than guessed.
- Per the project plan's own recommendation, cloud-side manual corrections
  apply only to the cloud's copy of attendance data for reporting and audit
  purposes; they do not modify the local PC's original SQLite records, since
  the local PC remains the source of truth for raw locally-recorded events
  (per the constitution's Principle I) and the cloud becomes the system of
  record for corrected/reported values going forward.
- Cloud user accounts (Owner/Admin/Viewer only — Guard is excluded, per the
  resolved clarification above) are provisioned by an Owner through an
  invitation flow within the dashboard itself; there is no public
  self-service sign-up.
- Existing local Admin/Guard accounts (from Feature 001/002) share the same
  four-role vocabulary carried in the JWT scheme, but this feature does not
  require merging or single-sign-on between the local PC's user store and the
  cloud's user store; a person may need separate
  credentials for each.
- The exact visual mockup for printed/PDF reports (logo placement, precise
  layout) is validated separately with the client before final styling; this
  spec fixes only the required content fields, not the pixel-level design.

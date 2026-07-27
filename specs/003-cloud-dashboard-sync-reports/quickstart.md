# Quickstart: Cloud Dashboard, Sync, and Reports

Manual/end-to-end validation scenarios for this feature, one per user story
plus the key edge cases. Assumes `backend/` (Feature 001) is already running
locally and `cloud-backend/` + `cloud-dashboard/` have been implemented per
`plan.md`.

## Prerequisites

- Local PC backend running (`backend/`) with at least one employee enrolled
  and able to record attendance (Feature 001/002 already validated).
- Cloud backend running (`cloud-backend/`) against a PostgreSQL database (or
  SQLite for a quick local trial), with at least one bootstrap Owner account
  seeded.
- A site sync API key configured identically in both `backend/`'s settings
  (`LOCAL_ATTENDANCE_SYNC_API_KEY` or equivalent, per tasks.md) and
  `cloud-backend/`'s settings.
- Cloud dashboard (`cloud-dashboard/`) built and pointed at the cloud
  backend's URL.

## Scenario 1 — Sync survives an offline gap (User Story 1, P1)

1. Confirm the local PC has internet access; record one arrival for a test
   employee via the guard PWA or a direct `POST /attendance/verify` call.
2. Wait for the next sync cycle (or trigger it manually if a manual-trigger
   task/endpoint exists) and confirm the event appears in the cloud
   dashboard's employee history, matching employee, type, and timestamp.
3. Disconnect the local PC's internet access (or point its sync target at an
   unreachable URL). Record two more attendance events (one arrival, one
   departure for a different employee) while "offline."
4. Confirm both events are stored locally (`synced = false`) and visible in
   the local PC's own views, but not yet in the cloud dashboard.
5. Restore internet access. Wait for sync to catch up. Confirm both events
   now appear in the cloud exactly once each (no duplicates), and that the
   local records are now marked `synced = true`.
6. Re-run the same sync push manually a second time (simulating a retry of
   an already-delivered batch). Confirm the cloud data is unchanged — no
   duplicate rows appear.

**Expected outcome**: SC-001 and SC-002 hold — all three events end up in the
cloud exactly once, survived the offline gap, and a retried push is a no-op.

## Scenario 2 — Generate and export a report (User Story 2, P2)

1. With at least a few days of synced attendance data for 2+ employees
   (including at least one incomplete pair — an arrival with no matching
   departure), log into the cloud dashboard as an Owner, Admin, or Viewer.
2. Request the daily report for a date with known data. Confirm every
   employee's arrival/departure appears, and the incomplete pair is flagged.
3. Request a custom-period report scoped to a single employee across
   several days. Confirm only that employee's data appears, matching the
   known test data.
4. Export the daily report as PDF. Confirm the file opens and contains:
   company name, the period, the arrival/departure table, a missing-record
   note for the incomplete pair, the generation date, and a signature area
   (FR-014).
5. Export the same report as Excel. Confirm the spreadsheet's rows match the
   on-screen report exactly.
6. Print the report directly from the dashboard (browser print dialog or
   print-preview) and confirm the layout matches the PDF export.
7. Log in as a Viewer and repeat steps 2–6. Confirm every action succeeds,
   and confirm no correction/edit/user-management control is visible or
   reachable anywhere in the flow.

**Expected outcome**: SC-003 and SC-004 hold.

## Scenario 3 — Manual correction with audit trail (User Story 3, P3)

1. As an Owner or Admin, find a synced attendance event and add a correction
   (e.g., correct its timestamp) with a reason.
2. Confirm the employee's attendance history now shows the corrected value.
3. Open the audit trail for that employee. Confirm it shows the original
   value, the new value, the reason, the author, and the timestamp of the
   change.
4. Add a second correction to the *same* event (e.g., change its type).
   Confirm the audit trail now shows both corrections in order, not just the
   latest.
5. Add a missing-departure correction for an employee with no departure
   event that day. Confirm a new attendance record appears in their history,
   marked as manually corrected.
6. Confirm (by inspecting the local PC's SQLite database or its API) that
   none of the above corrections altered any local record (FR-022) — the
   local PC's original data is untouched.
7. Log in as a Viewer. Confirm no correction control is visible, and a
   direct `POST /attendance/corrections` call with the Viewer's token is
   rejected with 403.

**Expected outcome**: SC-005 holds; local PC data is provably unaffected.

## Scenario 4 — RBAC enforcement, including Guard rejection (User Story 4, P4)

1. As an Owner, invite a new user with the Admin role. Confirm they can log
   in and perform Admin-scoped actions (view employees, create corrections,
   generate/export reports) but cannot reach user-management screens.
2. As the Owner, change that user's role to Viewer. Confirm their next
   dashboard action reflects read-only access immediately.
3. As the Owner, revoke that user's access. Confirm they can no longer log
   in, and any already-open session is denied on its next action (SC-008).
4. Attempt to call any dashboard-only endpoint (e.g.,
   `GET /attendance/corrections/{employee_id}`) directly with a valid local
   PC Guard JWT (obtained from the local PC's own `/auth/login`). Confirm the
   cloud backend rejects it — Guard accounts have no cloud dashboard access
   at all (FR-023).
5. Attempt to invite a new user with role `guard` via `POST /users`. Confirm
   the cloud backend rejects this — only `owner`, `admin`, and `viewer` are
   valid cloud roles.

**Expected outcome**: SC-006 holds; the backend — not the UI — is what
actually blocks unauthorized actions in every case above.

## Edge case checks

- **Cloud backend unreachable**: stop `cloud-backend/` entirely and confirm
  the local guard workflow (search, verify, record attendance) still works
  end-to-end on the local PC, unaffected (SC-007).
- **Employee force-deleted locally after syncing**: use the local admin's
  existing force-delete capability on an employee who already has synced
  history, then confirm the cloud dashboard still shows that employee's
  historical attendance/reports rather than erroring or silently dropping
  the data.
- **Report requested for a not-yet-synced period**: with sync paused,
  request a report covering "today." Confirm the report clearly indicates
  it may be incomplete (FR-017) rather than silently presenting partial data
  as final.

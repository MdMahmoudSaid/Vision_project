# Feature Specification: Guard PWA Local Interface

**Feature Branch**: `002-guard-pwa-interface`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Feature 002: Guard PWA local interface. Build the guard-facing PWA for the local attendance system. It connects to the local PC API from Feature 001 on the same Wi-Fi network. The guard can log in, search/select an active employee by name or employee number, choose arrival or departure, trigger facial verification, see clear success/failure/duplicate results, view recent shift activity, and optionally access employee creation + face enrollment if authorized. The UI must be extremely simple: large controls, no technical jargon, no configuration screens for guards, and the main attendance flow should take at most three taps after login. The PWA must consume the existing local API contract from specs/001-local-attendance-core/contracts/local-api.yaml and must not implement facial recognition, camera access, offline phone storage, cloud dashboard, reports, manual corrections, or NVR/video features."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record Attendance in Three Taps (Priority: P1)

A guard who is already logged in selects an active employee, chooses arrival or
departure, and triggers verification. The face capture and comparison happen
on the local PC (the fixed camera is not part of this interface); the guard
only sees a clear success, failure, or duplicate-blocked result.

**Why this priority**: This is the core reason the guard uses the interface at
all. Every shift depends on this flow being fast and unambiguous.

**Independent Test**: Can be tested by logging in as a guard, selecting one
active employee with a usable facial reference, choosing arrival, triggering
verification, and confirming the result screen matches the outcome from the
local API in at most three taps after login (select employee, choose type,
trigger verification).

**Acceptance Scenarios**:

1. **Given** a logged-in guard and an active employee with a usable facial
   reference, **When** the guard selects the employee, chooses "arrival," and
   triggers verification, **Then** the interface shows a clear success result
   within the time the local API takes to respond, with no additional
   required taps.
2. **Given** a logged-in guard, **When** verification fails, **Then** the
   interface shows a clear failure result and does not display or imply that
   an attendance event was recorded.
3. **Given** a logged-in guard, **When** the local API reports the attempt as
   duplicate-blocked, **Then** the interface shows a message explaining that
   recent attendance was already recorded for that employee, distinct from a
   failure message.
4. **Given** a logged-in guard, **When** the local API is unreachable over the
   local Wi-Fi network, **Then** the interface shows a clear connection
   problem message instead of a silent failure or a misleading success/failure
   result.

---

### User Story 2 - Find the Right Employee Quickly (Priority: P2)

A guard searches for an employee by name or employee number from a short list
and selects the correct one before choosing arrival or departure.

**Why this priority**: The attendance flow in User Story 1 depends on the
guard being able to find the correct employee quickly, especially at a busy
post with many employees.

**Independent Test**: Can be tested by searching a set of employees by partial
name and by employee number and confirming only active employees matching the
search appear, ready for selection.

**Acceptance Scenarios**:

1. **Given** a logged-in guard and multiple active employees, **When** the
   guard types part of a name or employee number, **Then** the interface shows
   matching active employees only.
2. **Given** an inactive employee exists, **When** the guard searches by that
   employee's name, **Then** the inactive employee does not appear as
   selectable for attendance.
3. **Given** no employees match the search text, **When** the guard views the
   results, **Then** the interface clearly indicates no matches instead of
   showing an empty or confusing screen.

---

### User Story 3 - Review Recent Shift Activity (Priority: P3)

A logged-in guard or administrator reviews a simple list of recent local
attendance activity, seeing successful attendance events and failed or
duplicate-blocked attempts clearly labeled.

**Why this priority**: Local visibility lets the guard confirm their own
actions were recorded correctly and answer immediate questions during a
shift, without needing separate reporting tools.

**Independent Test**: Can be tested by generating one successful verification,
one failed verification, and one duplicate-blocked attempt, then opening the
shift activity view and confirming each outcome is labeled distinctly.

**Acceptance Scenarios**:

1. **Given** recent local activity exists, **When** the user opens shift
   activity, **Then** the interface lists recent events with employee name,
   type, time, and a plainly worded outcome.
2. **Given** a failed or duplicate-blocked attempt exists, **When** the user
   views shift activity, **Then** it is visibly distinguished from a
   successful attendance event, not presented as recorded attendance.

---

### User Story 4 - Manage Employees and Enroll Faces When Authorized (Priority: P4)

An authorized user (administrator) uses the same interface to create a new
employee profile and start face enrollment for that employee, while a guard
without that authorization does not see these actions at all.

**Why this priority**: Employee setup must happen somewhere convenient for the
person on-site, but it is a lower-frequency action than daily attendance
recording and must never be exposed to unauthorized guards.

**Independent Test**: Can be tested by logging in as an administrator,
creating an employee, starting face enrollment, and confirming the same
actions are absent from the interface when logged in as a guard.

**Acceptance Scenarios**:

1. **Given** a logged-in administrator, **When** they open the interface,
   **Then** employee creation and face enrollment actions are visible and
   usable.
2. **Given** a logged-in guard without administrator authorization, **When**
   they use the interface, **Then** employee creation and face enrollment
   actions are not shown.
3. **Given** an administrator creates an employee, **When** they start face
   enrollment for that employee, **Then** the interface shows whether the
   resulting facial reference is usable or must be repeated, using the same
   plain wording as the attendance result messages.

### Edge Cases

- The local API is unreachable or slow to respond over the local Wi-Fi
  network.
- The guard's session/login expires while using the interface.
- Face enrollment or verification is rejected by the local API because of
  capture problems on the local PC (no face, unusable image); the guard-facing
  wording must not require technical understanding of cameras or models.
- An employee search returns a very large number of matches.
- The guard double-taps the verify action before a result is shown.
- A guard attempts to reach an administrator-only action directly (for
  example, through a saved link) despite it not being shown in their normal
  navigation.
- The screen is used on a small phone screen versus a larger tablet or PC
  browser window.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST let a local user log in with the same credentials
  used by the local attendance API and MUST NOT provide a separate
  registration flow.
- **FR-002**: System MUST end the session and require re-login when the
  local API reports the session/token as invalid or expired.
- **FR-003**: System MUST let a logged-in user search and select an active
  employee by partial name or employee number before starting attendance
  verification.
- **FR-004**: System MUST NOT present inactive employees as selectable for
  attendance verification.
- **FR-005**: System MUST require the user to explicitly choose arrival or
  departure before triggering verification, and MUST NOT infer the type
  automatically.
- **FR-006**: System MUST trigger facial verification for the selected
  employee and type through the local attendance API and MUST NOT perform any
  facial capture, comparison, or camera access itself.
- **FR-007**: System MUST display success, failure, and duplicate-blocked
  verification outcomes with plainly worded, visually distinct messages.
- **FR-008**: System MUST display a clear connection-problem message when the
  local API cannot be reached, instead of an ambiguous or silent failure.
- **FR-009**: System MUST let a logged-in user view a list of recent local
  shift activity, showing employee, type, time, and outcome for each entry.
- **FR-010**: System MUST visually distinguish failed and duplicate-blocked
  attempts from successful attendance events in the shift activity view.
- **FR-011**: System MUST show employee creation and face enrollment actions
  only to users authorized for those actions, and MUST hide them from guards
  who are not authorized.
- **FR-012**: System MUST rely on the local attendance API's own authorization
  checks for every protected action; hiding an action in the interface MUST
  NOT be the only protection against an unauthorized user performing it.
- **FR-013**: System MUST let an authorized user create an employee profile
  and start face enrollment for that employee using the same plain,
  non-technical wording as the rest of the interface.
- **FR-014**: System MUST keep the main attendance flow (select employee,
  choose type, trigger verification, see result) to at most three user
  actions after login under normal conditions with a short employee list or a
  successful search.
- **FR-015**: System MUST use large, touch-friendly controls and avoid
  technical jargon, configuration screens, or dense management concepts in
  any guard-facing screen.
- **FR-016**: System MUST NOT implement or embed facial recognition, camera
  access, offline local storage of attendance data, cloud dashboard features,
  reports, manual corrections, or NVR/video functionality; all attendance and
  verification data comes from the local attendance API.
- **FR-017**: System MUST NOT store or cache facial reference data or other
  biometric information on the device running the interface.

### Key Entities *(include if feature involves data)*

- **Guard Session**: The logged-in state of a local user in the interface,
  including their role, used to decide which actions are shown and to detect
  when re-login is required.
- **Employee Search Result**: A lightweight, display-only view of an active
  employee (name, employee number, department) used for selection before
  verification; excludes any biometric data.
- **Attendance Verification Outcome**: The plain-language result shown to the
  guard after triggering verification: success, failure, or
  duplicate-blocked, mirrored from the local attendance API's response.
- **Shift Activity Item**: A single row in the recent activity view showing
  employee, type, time, and outcome, mirrored from the local attendance API.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A guard who has never used the interface before can complete a
  successful attendance recording in at most three taps after login, without
  needing instructions beyond on-screen labels.
- **SC-002**: 100% of verification results shown to the guard (success,
  failure, duplicate-blocked) are visually and textually distinguishable from
  each other in usability review.
- **SC-003**: 100% of unauthorized attempts to reach employee creation or
  face enrollment actions from the guard role are blocked, both by the
  interface not showing them and by the underlying API rejecting the request.
- **SC-004**: A guard can find and select the correct employee from a search
  of at least 50 active employees in under 10 seconds.
- **SC-005**: The interface remains fully usable (no horizontal scrolling, no
  unreadable text, no overlapping controls) on both a small phone-sized
  screen and a larger tablet or PC browser window.
- **SC-006**: When the local API is unreachable, 100% of attendance and
  activity screens show a clear connection-problem message within a few
  seconds instead of appearing to hang or silently fail.

## Assumptions

- The local attendance API from Feature 001 is already running and reachable
  on the same local Wi-Fi network; this feature does not configure networking,
  install certificates, or manage the local PC.
- Local user accounts (guard and administrator) already exist, created
  through Feature 001's local account provisioning; this feature has no
  account registration screen of its own.
- Only the two local roles from Feature 001 apply here: guard and
  administrator. Guards use the attendance and shift-activity flows;
  administrators additionally see employee creation and face enrollment.
- The interface is reachable from a web browser on a phone, tablet, or PC on
  the same local network; native app store distribution and installability
  details are not required for this feature's user value.
- All facial capture and comparison happen on the local PC's fixed camera
  through Feature 001's API; this feature never accesses a camera or
  processes biometric data on the device running the interface.
- Cloud dashboard, reports, exports, manual corrections, and NVR/video review
  remain separate, later features and are not exposed anywhere in this
  interface.

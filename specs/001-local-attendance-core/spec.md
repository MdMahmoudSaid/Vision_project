# Feature Specification: Local Attendance Core

**Feature Branch**: `001-local-attendance-core`

**Created**: 2026-07-20

**Status**: Draft

**Input**: User description: "Feature 001: noyau local de pointage. Covers local PC attendance foundations, fixed-camera facial enrollment and verification, employee records, arrival/departure events, verification attempt logging, and duplicate-submission protection."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record Verified Attendance (Priority: P1)

A guard selects an existing employee, chooses whether the employee is arriving
or departing, and triggers a facial verification from the fixed camera. If the
captured face matches the selected employee, the system records the attendance
event and immediately confirms the result to the guard. If the verification
fails, the system rejects the attendance event while still keeping a trace of
the failed attempt.

**Why this priority**: This is the core business value of the product: proving
that a selected employee was physically present at the moment of arrival or
departure.

**Independent Test**: Can be tested with one registered employee, one authorized
guard, and the fixed camera by performing one successful arrival, one successful
departure, and one failed verification attempt.

**Acceptance Scenarios**:

1. **Given** an active employee with a valid facial reference and an authorized guard, **When** the guard selects "arrival" and verification succeeds, **Then** the system records one arrival event linked to the employee, guard, timestamp, and verification attempt.
2. **Given** an active employee with a valid facial reference and an authorized guard, **When** the guard selects "departure" and verification succeeds, **Then** the system records one departure event linked to the employee, guard, timestamp, and verification attempt.
3. **Given** an employee selected by the guard, **When** the captured face does not verify as that employee, **Then** the system logs the failed verification attempt and does not create an attendance event.
4. **Given** the internet connection is unavailable, **When** the guard completes a successful local verification, **Then** the attendance event and attempt are still stored locally and visible to local operations.

---

### User Story 2 - Register Employee Facial Reference (Priority: P2)

An authorized user creates or updates an employee profile and captures multiple
face samples from the fixed camera so the employee can later be verified during
attendance.

**Why this priority**: Verified attendance is impossible until employees have
trusted local identity records and facial references.

**Independent Test**: Can be tested by creating a new employee, capturing the
employee's face samples, confirming the profile is active, and using that
employee in the verified attendance flow.

**Acceptance Scenarios**:

1. **Given** an authorized user and a person physically present at the fixed camera, **When** the user enters the required employee details and completes face capture, **Then** the system stores an active employee profile with a usable facial reference.
2. **Given** an existing active employee whose appearance needs refreshing, **When** an authorized user performs face re-enrollment, **Then** future verification uses the updated facial reference without losing the employee's attendance history.
3. **Given** a face is not visible or not usable during enrollment, **When** the user attempts to save the facial reference, **Then** the system rejects the enrollment and explains that the capture must be repeated.

---

### User Story 3 - Prevent Duplicate Submissions (Priority: P3)

The system prevents repeated successful attendance submissions for the same
employee and attendance type inside a short configurable time window, while
still allowing legitimate later arrival and departure records.

**Why this priority**: Duplicate protection preserves trust in attendance data
and reduces accidental repeated taps by the guard.

**Independent Test**: Can be tested by submitting the same employee and same
attendance type twice inside the duplicate window, then trying again after the
window expires.

**Acceptance Scenarios**:

1. **Given** an employee has just recorded a successful arrival, **When** the guard submits another successful arrival for the same employee inside the duplicate window, **Then** the system rejects the duplicate event and does not create a second attendance event.
2. **Given** a duplicate submission is rejected, **When** the system reports the result to the guard, **Then** the message clearly explains that the recent attendance was already recorded.
3. **Given** the duplicate window has expired, **When** the guard submits a valid attendance event, **Then** the system evaluates it normally instead of blocking it only because of the older record.

---

### User Story 4 - Review Local Shift Activity (Priority: P4)

A guard or local administrator can view recent local attendance activity for the
current shift, including successful attendance events and failed verification
attempts, to confirm what has happened at the post.

**Why this priority**: Local visibility helps the guard recover from confusion,
answer immediate operational questions, and confirm that the system is recording
events during internet outages.

**Independent Test**: Can be tested after generating one successful attendance
event and one failed verification attempt, then viewing the local activity list.

**Acceptance Scenarios**:

1. **Given** attendance activity exists for the current shift, **When** the authorized user opens local shift activity, **Then** the system shows recent events with employee, type, time, guard, and outcome.
2. **Given** a failed verification attempt exists, **When** the authorized user reviews local activity, **Then** the failed attempt is visible as a failed attempt and is not presented as attendance.

### Edge Cases

- The fixed camera is unavailable, disconnected, blocked, or returns no usable image.
- The captured image contains no face, multiple faces, or a face that cannot be evaluated.
- The selected employee is inactive or has no usable facial reference.
- The guard is not authorized or the session is expired.
- Local storage is temporarily unavailable or cannot persist the result.
- The same guard taps the verify action repeatedly while a verification is still in progress.
- The same employee legitimately needs both arrival and departure on the same day.
- The system clock is incorrect enough to make attendance records unreliable.
- Internet is unavailable during recording; local operation must continue.
- A failed attempt happens repeatedly for the same selected employee.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow an authorized local user to sign in and receive permissions appropriate to the user's local role.
- **FR-002**: System MUST allow authorized users to create and update employee profiles with full name, employee number, optional department, job title, phone, notes, active status, and registration metadata.
- **FR-003**: System MUST generate a unique employee number when one is not provided by the client user.
- **FR-004**: System MUST allow authorized users to capture and store a usable facial reference for an employee from the fixed camera.
- **FR-005**: System MUST allow authorized users to re-enroll an existing employee's facial reference without deleting the employee's existing attendance history.
- **FR-006**: System MUST reject employee face enrollment when the capture is unusable, including no face, multiple faces, or insufficient face quality.
- **FR-007**: System MUST allow a guard to search or select an active employee before starting attendance verification.
- **FR-008**: System MUST require the guard to explicitly choose either arrival or departure before verification starts.
- **FR-009**: System MUST capture the face from the fixed camera at the time of verification and compare it to the selected employee's stored facial reference.
- **FR-010**: System MUST record every verification attempt, successful or failed, with employee, guard, requested attendance type, timestamp, outcome, confidence or similarity result when available, and failure reason when applicable.
- **FR-011**: System MUST create an attendance event only when facial verification succeeds for the selected employee.
- **FR-012**: System MUST NOT create an attendance event when verification fails, the camera capture is unusable, the employee is inactive, or the user is unauthorized.
- **FR-013**: System MUST link each successful attendance event to the verification attempt that produced it.
- **FR-014**: System MUST prevent duplicate successful attendance events for the same employee and same attendance type inside the configured duplicate window.
- **FR-015**: System MUST use 60 seconds as the default duplicate window unless changed during later configuration planning.
- **FR-016**: System MUST persist local employee records, facial references, verification attempts, and attendance events without requiring internet connectivity.
- **FR-017**: System MUST mark locally stored records that still need later synchronization without depending on cloud availability for local attendance recording.
- **FR-018**: System MUST provide recent local shift activity showing successful attendance events and failed verification attempts separately.
- **FR-019**: System MUST protect facial reference data and authentication secrets from exposure to guard-facing clients.
- **FR-020**: System MUST produce timestamps precise enough for later manual comparison with the client's separate video surveillance system.
- **FR-021**: System MUST provide clear success, failure, duplicate, and retry outcomes suitable for a simple guard-facing UI.
- **FR-022**: System MUST keep all raw attendance data local-first; cloud reports, manual corrections, and exports are outside this feature except for preparing local records for future sync.

### Key Entities *(include if feature involves data)*

- **Employee**: A person whose attendance can be verified. Key attributes include identity details, employee number, active status, registration metadata, and facial reference status.
- **Local User**: A local account used by a guard or administrator. Key attributes include username, role, active status, and authentication credentials.
- **Facial Reference**: The stored representation created from one or more accepted face captures for an employee and used for future verification.
- **Verification Attempt**: A record of every attempted facial verification, successful or failed, including selected employee, guard, requested type, time, result, score when available, and failure reason when applicable.
- **Attendance Event**: A confirmed arrival or departure created only from a successful verification attempt.
- **Duplicate Window Setting**: The configured period used to reject repeated successful submissions for the same employee and attendance type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A guard can complete the primary attendance flow from employee selection to visible result in under 5 seconds during realistic local operation.
- **SC-002**: 100% of failed facial verifications in acceptance testing are logged as failed attempts and create zero attendance events.
- **SC-003**: 100% of successful facial verifications in acceptance testing create exactly one attendance event linked to its verification attempt.
- **SC-004**: Repeating the same successful employee/type submission inside the duplicate window creates zero additional attendance events in acceptance testing.
- **SC-005**: A new employee can be registered with identity details and a usable facial reference in under 1 minute when the camera view is suitable.
- **SC-006**: Local attendance recording continues during an internet outage, with all created records still available locally after the outage scenario.
- **SC-007**: Local role checks prevent unauthorized users from creating employees, enrolling faces, or recording attendance in 100% of role-based acceptance checks.
- **SC-008**: Local shift activity distinguishes successful attendance events from failed verification attempts in all acceptance scenarios.

## Assumptions

- The fixed camera is installed, aimed at the attendance position, and physically connected to the local PC before acceptance testing.
- The guard and employee are physically present during attendance verification; automated liveness detection is not required for V1.
- The guard-facing PWA is a separate feature and will consume the contracts generated from this feature.
- Cloud dashboard, manual corrections, reports, exports, and printing are separate later features.
- The local system uses a default duplicate window of 60 seconds until an administrator-facing configuration feature defines another value.
- Employee numbers are unique locally; the exact numbering format may be finalized during Phase 0 planning without changing this feature's user value.
- Raw video storage, video replay, NVR access, and video dispute review are outside this feature and outside the project scope.

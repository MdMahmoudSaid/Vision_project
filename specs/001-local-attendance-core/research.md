# Research: Local Attendance Core

## Decision: Use a local FastAPI service for the guard-facing backend

**Rationale**: The project plan already selects a Python backend on the local
PC. FastAPI fits the local API use case, produces OpenAPI contracts for the
intern's frontend work, and supports dependency-based authorization.

**Alternatives considered**: Flask would be smaller but would require more
manual contract and validation structure. A desktop-only application would make
the guard PWA integration harder.

## Decision: Use SQLite as the local source of truth

**Rationale**: The feature needs durable local storage without internet or
server administration. SQLite is sufficient for a single guard-post PC, supports
transactional writes, and keeps deployment simple.

**Alternatives considered**: PostgreSQL would be stronger for concurrent
multi-client deployments but adds local installation and maintenance overhead.
Flat files would be simpler initially but too risky for audit records,
relationships, and duplicate prevention.

## Decision: Store facial references locally as serialized embeddings

**Rationale**: The local PC performs both enrollment and verification. Storing
face embeddings locally supports offline verification and avoids sending
biometric reference data to the guard-facing client.

**Alternatives considered**: Storing raw face images increases privacy and
storage risk. Recomputing references from external files is fragile and does not
fit local-first operation. Cloud-only references would violate offline
attendance requirements.

## Decision: Wrap camera and face processing behind service interfaces

**Rationale**: Hardware and face recognition are the highest-variance parts of
the feature. Interfaces allow the implementation to use OpenCV and DeepFace in
production while contract, unit, and integration tests use deterministic mocks.

**Alternatives considered**: Calling hardware and recognition libraries directly
inside API handlers would be faster to write but harder to test and debug.

## Decision: Separate verification attempts from attendance events

**Rationale**: The constitution requires all attempts to be logged and failed
verifications to create no attendance. Separate entities make the audit trail
clear: every attempt is recorded, and only successful attempts can produce an
attendance event.

**Alternatives considered**: A single attendance table with status flags would
mix failures and confirmed attendance, making reports and audit checks easier to
misread.

## Decision: Enforce duplicate blocking at attendance creation time

**Rationale**: Duplicate protection must be authoritative and cannot depend on
frontend behavior. The attendance creation service will check recent successful
events for the same employee and type inside the configured window before
writing a new event.

**Alternatives considered**: UI-only throttling is easy to bypass and does not
protect against repeated API calls. Database-only uniqueness is too rigid
because the window is time-based and configurable.

## Decision: Use local Admin and Guard roles for this feature

**Rationale**: The feature only covers the local PC core. Local Admin can manage
employees and facial references; Guard can search employees, verify attendance,
and view shift activity. Cloud Owner and Viewer roles are deferred to dashboard
features.

**Alternatives considered**: Implementing the full cloud role matrix locally
would add scope before the cloud dashboard exists. No local RBAC would violate
the constitution and make future UI controls unsafe.

## Decision: Treat local HTTPS as deployment/stabilization work, not core logic

**Rationale**: HTTPS is required for the installed guard PWA and on-site
deployment, but this feature can define and test the local API behavior before
the certificate strategy is finalized.

**Alternatives considered**: Blocking this feature on certificate choice would
slow the backend core. Ignoring HTTPS entirely would break later PWA deployment,
so it remains a Phase 0/deployment decision outside this feature's implementation
logic.

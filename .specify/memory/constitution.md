<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Template placeholder principles -> I. Local Attendance Truth and Offline Reliability
- Template placeholder principles -> II. Verified Presence and Complete Auditability
- Template placeholder principles -> III. Backend-Enforced RBAC and Data Protection
- Template placeholder principles -> IV. Guard-First Simplicity and Contract-First UI
- Template placeholder principles -> V. Incremental SDD and Testable Delivery
Added sections:
- Project Scope and Technical Constraints
- Development Workflow and Quality Gates
Removed sections:
- Placeholder template examples and unresolved placeholder tokens
Templates requiring updates:
- .specify/templates/plan-template.md: validated, no update required
- .specify/templates/spec-template.md: validated, no update required
- .specify/templates/tasks-template.md: validated, no update required
Runtime guidance requiring updates:
- README.md: validated, no update required
- docs/plan_pointage_facial.md: source document, no update required
Follow-up TODOs:
- Resolve Phase 0 decisions before the first implementation plan: local HTTPS approach,
  cloud hosting provider, printed report mockup, duplicate-submission window,
  employee-numbering scheme, and whether cloud corrections sync back to the local PC.
-->
# Facial Attendance System Constitution

## Core Principles

### I. Local Attendance Truth and Offline Reliability
The local PC MUST remain the source of truth for raw attendance events and facial
verification attempts. The guard workflow MUST work on the local Wi-Fi network
without internet access: guard PWA -> local PC API -> USB webcam -> local
SQLite. Cloud connectivity MAY enrich management dashboards, reports, exports,
and corrections, but it MUST NOT be required for the core act of recording a
verified arrival or departure.

The system MUST store every locally created attendance event, verification
attempt, and correction durably before attempting cloud synchronization. Sync
jobs MUST be idempotent and MUST NOT create duplicates when internet returns.
Any feature that weakens local operation, moves raw attendance authority to the
cloud, or depends on phone-side facial recognition violates this principle.

### II. Verified Presence and Complete Auditability
The system MUST only create an attendance event after the selected employee,
the selected event type, and the captured face verification result are all
known. A failed facial verification MUST be logged as a verification attempt
and MUST NOT create an attendance event. The system MUST never infer arrival or
departure automatically; the guard explicitly chooses the type.

Corrections MUST be non-destructive. Manual additions, time corrections, and
arrival/departure type changes MUST preserve the original record, require a
reason, and record who performed the action, when it happened, the previous
value, and the new value. Timestamps on attendance events and verification
attempts MUST be precise enough to allow manual cross-checking with the
client's separate NVR system.

### III. Backend-Enforced RBAC and Data Protection
Authorization MUST be enforced by backend APIs on every protected operation.
UI hiding is allowed for usability, but it MUST NOT be the security boundary.
JWT or equivalent session tokens MUST carry roles, and every endpoint MUST
validate the effective role before reading or changing protected data.

The V1 role model is Owner, Admin, Guard, and Viewer in the cloud, plus local
Admin and Guard accounts on the PC. Owners may manage users and all management
data. Admins may manage employees, faces, corrections, reports, and attendance
operations according to the feature scope. Guards may perform the guard
workflow and view their shift activity. Viewers may read and export reports but
MUST NOT modify data.

Face embeddings, authentication secrets, and audit data MUST be treated as
sensitive. Passwords MUST be hashed, secrets MUST NOT be committed, and
biometric reference data MUST NOT be exposed to frontend clients except through
purpose-built verification or registration APIs.

### IV. Guard-First Simplicity and Contract-First UI
The guard PWA MUST be designed for repeated operational use by a non-technical
security guard. The primary flow MUST remain: select employee, choose arrival
or departure, verify. The guard UI MUST avoid configuration screens, jargon,
and dense management concepts. It MUST use large controls, immediate success
or failure feedback, and at most three primary actions per screen.

Frontend work by the intern or any UI contributor MUST start from stable API
contracts, mock responses, and acceptance scenarios. Business rules such as
facial thresholds, duplicate blocking, attendance completeness, corrections,
and RBAC decisions MUST live in backend logic, not only in frontend state.

### V. Incremental SDD and Testable Delivery
Each Spec Kit feature MUST be independently valuable and testable. Large
project phases SHOULD be grouped into deliverable features such as local
attendance core, guard PWA, corrections and audit, cloud dashboard and reports,
and deployment stabilization. A generated plan MUST include acceptance checks
that can prove the feature without relying on unfinished future features.

Tasks MUST be ordered so shared foundations come first, followed by user
stories in priority order. Critical behavior MUST have focused tests or manual
validation steps: facial verification success and failure, duplicate blocking,
RBAC denials, non-destructive corrections, sync idempotency, PDF/Excel report
content, and the end-to-end guard flow completing in under five seconds under
realistic local conditions.

## Project Scope and Technical Constraints

The confirmed V1 architecture is a USB webcam connected directly to a local PC,
a local FastAPI backend with facial processing, SQLite for local persistence, a
React/Vite PWA for the guard on the local network, and a cloud FastAPI plus
PostgreSQL management dashboard for synchronized reporting and administration.

The client NVR and video surveillance system are explicitly outside this
project's technical scope. This project MUST NOT build video storage, video
playback, NVR integration, RTSP processing, or a dispute-review video player.
The project is responsible for reliable timestamped attendance and verification
records that can be manually compared with the external NVR when needed.

The V1 scope includes roles and permissions, manual corrections with audit
trail, daily/weekly/monthly/custom reports, PDF export, Excel export, and
printing support. These items MUST NOT be silently deferred unless the plan and
constitution are explicitly amended.

Phase 0 MUST resolve the following before implementation plans are treated as
ready: local HTTPS/PWA install strategy, cloud hosting provider and budget,
printed report layout, duplicate-submission window, employee-number generation,
and whether cloud-side corrections sync back to the local PC or remain
cloud-only for final reporting.

## Development Workflow and Quality Gates

Spec Kit artifacts MUST be produced in this order for each feature:
specification, clarification when needed, implementation plan, tasks, analysis,
then implementation. The constitution MUST be loaded during planning and
analysis. Any conflict with this constitution is a planning defect, not an
implementation detail.

Specifications MUST describe user value, actors, data, acceptance scenarios,
edge cases, and measurable success criteria without leaking unnecessary
implementation code. Plans MUST document contracts, data models, dependencies,
security assumptions, and validation scenarios. Tasks MUST include concrete
file paths and preserve independently testable user story slices.

Before implementation starts for a feature, the team MUST confirm that API
contracts needed by frontend work are stable enough for mock-driven UI
development. Before a feature is considered complete, it MUST pass its quickstart
or equivalent validation scenario and any constitution-relevant checks for
auditability, RBAC, offline behavior, and user-facing simplicity.

## Governance

This constitution governs all specs, plans, tasks, and implementation decisions
for the facial attendance system. When a plan document, generated task list, or
ad hoc implementation choice conflicts with this constitution, the constitution
takes precedence unless it is explicitly amended first.

Amendments require updating this file, recording the impact report at the top,
and reviewing affected templates or runtime guidance. Versioning follows
semantic versioning: MAJOR for principle removals or incompatible governance
changes, MINOR for new principles or materially expanded rules, and PATCH for
clarifications or wording-only changes.

Every feature review MUST check compliance with the five core principles. Any
exception MUST be documented in the implementation plan's Complexity Tracking
section with the rejected simpler alternative and the reason the exception is
necessary.

**Version**: 1.0.0 | **Ratified**: 2026-07-20 | **Last Amended**: 2026-07-20

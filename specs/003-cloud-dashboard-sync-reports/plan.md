# Implementation Plan: Cloud Dashboard, Sync, and Reports

**Branch**: `003-cloud-dashboard-sync-reports` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-cloud-dashboard-sync-reports/spec.md`

## Summary

Build the cloud side of the attendance system: a new cloud FastAPI backend
(PostgreSQL) that receives a one-way idempotent sync push from the local PC
(Feature 001), a management dashboard (Owner/Admin/Viewer) to browse synced
employees and attendance history, a non-destructive manual-correction
workflow with a full audit trail, and a reporting module (daily/weekly/
monthly/custom, PDF/Excel export, print) — matching
`docs/plan_pointage_facial.md` Phase 4 and the client's cahier de charge §14–16,
§20, §22. The Guard role is recognized by the cloud backend only to be
rejected; Guards continue to use exclusively the local PC/PWA. The local PC
remains the unmodified source of truth for raw attendance data; this feature
only adds a push and, on the cloud side, an additional corrected/reported
view on top.

Technical approach: a new `cloud-backend/` Python package mirroring
`backend/`'s existing FastAPI/SQLAlchemy/JWT/RBAC conventions, a new
`cloud-dashboard/` React/Vite/TypeScript app mirroring `frontend/`'s
conventions, and a small addition to the existing `backend/` (one schema
migration plus an in-process background sync-push loop). See
[research.md](./research.md) for the full rationale behind each choice.

## Technical Context

**Language/Version**: Python 3.11 (cloud backend, matching `backend/`'s
existing `requires-python = ">=3.11"`); TypeScript 5.x on Node.js 20 LTS
(cloud dashboard, matching `frontend/`).

**Primary Dependencies**: `cloud-backend/` — FastAPI, SQLAlchemy 2.x,
Alembic, Pydantic v2 + pydantic-settings, PyJWT, bcrypt, `psycopg[binary]`
(PostgreSQL driver, production only), Jinja2 + WeasyPrint (PDF export),
`openpyxl` (Excel export). `backend/` addition — `httpx` promoted from a
dev/test-only dependency to a runtime dependency (outbound sync push
client). `cloud-dashboard/` — React 18, Vite, React Router, same testing
stack as `frontend/` (Vitest, React Testing Library, MSW).

**Storage**: PostgreSQL in production for `cloud-backend/` (`DATABASE_URL`);
SQLite for automated tests, using the same DB-portable SQLAlchemy column
conventions `backend/`'s models already use (research.md §7). `backend/`'s
existing SQLite database gains exactly one new column
(`Employee.synced`, default `False`) via an Alembic migration.

**Testing**: pytest + FastAPI `TestClient`/`httpx` for `cloud-backend/`,
mirroring `backend/`'s existing test setup and its fake-camera/fake-face
patterns (adapted here to a fake sync-source and fake clock where needed for
report-period boundary tests). Vitest + React Testing Library + MSW for
`cloud-dashboard/`, mirroring `frontend/`'s existing setup.

**Target Platform**: `cloud-backend/` and `cloud-dashboard/` deployed to a
managed Linux container host (Render/Railway per
`docs/plan_pointage_facial.md` §5 — the specific provider is a deployment
detail decided during `tasks.md`/deployment, not fixed here). `backend/`'s
existing local PC process gains an in-process background sync loop — no new
process to install or keep alive on-site.

**Project Type**: Web service (new `cloud-backend/`) + web frontend (new
`cloud-dashboard/`), plus a minimal addition to the existing local `backend/`
(one migration, one new `sync/` module). Guard accounts and the guard PWA
(`frontend/`) are entirely untouched by this feature.

**Performance Goals**: Sync visibility within 5 minutes at least 95% of the
time when the local PC has connectivity (spec SC-001); report generation
under 5 seconds for a single-employee custom report and under 15 seconds for
a monthly organization-wide report under realistic data volumes (spec
SC-003).

**Constraints**: Cloud unavailability MUST NOT block the local guard
workflow (spec FR-004, SC-007). Sync MUST be idempotent, reusing each
record's existing local UUID as the cloud's primary key (spec FR-002,
research.md §3). All cloud RBAC decisions MUST be backend-enforced, never
UI-only (spec FR-018), and MUST reject Guard-role tokens outright (spec
FR-023). Corrections MUST be append-only/non-destructive and MUST NOT write
back to the local PC (spec FR-010, FR-022). Facial embeddings MUST NEVER be
transmitted to or stored in the cloud (spec Assumptions).

**Scale/Scope**: Single client deployment — one guard-post PC syncing to one
cloud tenant, a handful of Owner/Admin/Viewer cloud accounts, report volumes
bounded by one organization's roster (tens to low hundreds of employees).
Not a multi-tenant SaaS design.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Local Attendance Truth and Offline Reliability**: PASS. The local PC
  remains the only writer of raw attendance/verification data; sync is a
  one-way, idempotent push (spec FR-001–003) and the cloud being unreachable
  never blocks the local guard workflow (spec FR-004). This directly
  satisfies "Sync jobs MUST be idempotent and MUST NOT create duplicates"
  and "[cloud connectivity] MUST NOT be required for the core act of
  recording a verified arrival or departure."
- **II. Verified Presence and Complete Auditability**: PASS. Corrections are
  non-destructive: the original record is preserved, a reason is required,
  and who/when/previous-value/new-value are all recorded (spec FR-008–010,
  data-model.md `corrections` table) — this is exactly the constitution's
  correction requirement, now finally implemented (it was explicitly
  deferred out of Features 001/002). The constitution's force-delete
  exception is also respected: an employee force-deleted locally after
  syncing still has retrievable cloud history (spec Edge Cases), so the
  cloud's audit/reporting value isn't silently destroyed by a local
  administrative action it had no part in.
- **III. Backend-Enforced RBAC and Data Protection**: PASS. Every cloud
  endpoint enforces role checks server-side (spec FR-018); Guard-role tokens
  are recognized only to be rejected (spec FR-023, research.md §9); facial
  embeddings are never transmitted to or stored in the cloud at all (spec
  Assumptions) — stronger than the constitution's minimum requirement that
  biometric data merely not be exposed to frontend clients except through
  purpose-built APIs.
- **IV. Guard-First Simplicity and Contract-First UI**: PASS (with a scope
  note). The guard workflow itself is entirely unchanged and untouched by
  this feature. The cloud dashboard is a management tool for Owner/Admin/
  Viewer, not the guard-facing surface the constitution's simplicity rules
  are primarily about — but the same contract-first discipline still
  applies: `contracts/cloud-api.yaml` is frozen before UI work begins, so the
  intern can build against mocked responses exactly as in Feature 002.
- **V. Incremental SDD and Testable Delivery**: PASS. Four independently
  testable, priority-ordered user stories (sync, reports, corrections, RBAC/
  user management); each has its own quickstart validation scenario
  (quickstart.md) that does not depend on the others being complete first
  beyond the natural data dependency (sync must exist before there's
  anything to report on or correct).

No constitution violations. The cloud FastAPI + PostgreSQL architecture
itself is not a new complexity introduced by this plan — it is the V1
architecture the constitution's own "Project Scope and Technical
Constraints" section already commits to. Complexity Tracking is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-cloud-dashboard-sync-reports/
├── plan.md              # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   └── cloud-api.yaml    # Phase 1 output: full OpenAPI contract for cloud-backend
└── tasks.md              # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
cloud-backend/                        # NEW — cloud FastAPI service
├── pyproject.toml                     # mirrors backend/pyproject.toml's dependency style
├── alembic/
├── alembic.ini
├── src/
│   └── cloud_attendance/
│       ├── main.py                    # app factory, logging config (mirrors local_attendance/main.py)
│       ├── config.py                  # Settings: database_url, jwt_secret, sync_api_key(s)
│       ├── database.py                # engine/session, portable sqlite/postgres connect_args
│       ├── models/
│       │   ├── __init__.py            # Base, TimestampMixin, generate_uuid (same conventions)
│       │   ├── cloud_user.py           # CloudUser (owner|admin|viewer)
│       │   ├── synced_employee.py
│       │   ├── synced_verification_attempt.py
│       │   ├── synced_attendance_event.py
│       │   ├── correction.py
│       │   └── sync_ingest_log.py
│       ├── schemas/                    # Pydantic request/response models per contracts/cloud-api.yaml
│       │   ├── auth.py
│       │   ├── employee.py
│       │   ├── correction.py
│       │   ├── report.py
│       │   ├── sync.py
│       │   └── user.py
│       ├── auth/
│       │   ├── tokens.py               # mirrors local_attendance/auth/tokens.py
│       │   ├── password.py             # mirrors local_attendance/auth/password.py
│       │   └── dependencies.py         # require_owner, require_admin_or_owner, require_any_cloud_role, require_sync_api_key
│       ├── services/
│       │   ├── sync_ingest_service.py  # upsert-by-id batch ingestion (idempotent)
│       │   ├── employee_service.py
│       │   ├── correction_service.py   # append-only writes, validation rules from data-model.md
│       │   ├── report_service.py       # daily/weekly/monthly/custom aggregation + completeness
│       │   ├── export_service.py       # PDF (Jinja2 + WeasyPrint) and Excel (openpyxl) rendering
│       │   └── user_service.py         # invite/role-change/revoke
│       ├── api/
│       │   ├── auth.py
│       │   ├── sync.py
│       │   ├── employees.py
│       │   ├── corrections.py
│       │   ├── reports.py
│       │   └── users.py
│       └── templates/
│           └── report.html.jinja       # shared HTML/CSS source for on-screen, print, and PDF export
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

cloud-dashboard/                       # NEW — React + Vite management dashboard
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes.tsx
│   ├── api/
│   │   ├── client.ts                  # mirrors frontend/src/api/client.ts
│   │   ├── types.ts                   # generated from contracts/cloud-api.yaml
│   │   ├── auth.ts
│   │   ├── employees.ts
│   │   ├── corrections.ts
│   │   ├── reports.ts
│   │   └── users.ts
│   ├── auth/
│   │   └── SessionContext.tsx
│   ├── components/
│   │   ├── ReportTable.tsx
│   │   ├── CompletenessBadge.tsx
│   │   └── AuditTrailList.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── OverviewPage.tsx            # dashboard/overview-style landing page
│   │   ├── EmployeeListPage.tsx        # US1
│   │   ├── EmployeeHistoryPage.tsx     # US1, US3 (corrections entry point)
│   │   ├── ReportsPage.tsx             # US2: generate + export/print
│   │   └── UserManagementPage.tsx      # US4, Owner-only
│   └── styles/
└── tests/
    ├── unit/
    └── integration/                    # MSW-mocked against contracts/cloud-api.yaml

backend/                               # EXISTING — Feature 001, small addition only
├── alembic/versions/
│   └── xxxx_add_employee_synced_column.py   # NEW migration
└── src/local_attendance/
    ├── config.py                       # + sync_target_url, sync_api_key, sync_interval_seconds
    └── sync/                           # NEW module
        ├── __init__.py
        ├── client.py                   # httpx push of synced=false batches, upsert-safe retries
        └── scheduler.py                # in-process asyncio background loop, started from main.py

frontend/                               # EXISTING — untouched by this feature
```

**Structure Decision**: Two new top-level projects (`cloud-backend/`,
`cloud-dashboard/`) alongside the existing `backend/`/`frontend/`, each
mirroring the conventions of its existing sibling exactly (same dependency
choices, same test tooling, same auth/RBAC dependency shape) per research.md
§1–2. The only change to existing code is additive: one column, one new
`sync/` module, and a background task started at app startup in
`backend/`'s `main.py` — no existing endpoint, model, or test changes.

## Phase 0: Research

Captured in [research.md](./research.md): cloud stack/package layout,
cloud dashboard frontend stack, sync transport/idempotency design, the new
`Employee.synced` column, sync scheduling mechanism, machine-to-machine sync
authentication, PostgreSQL/SQLite test portability, PDF/Excel libraries,
cloud RBAC dependency shape, the correction data model, and printed-report
content fields. All previously-open questions relevant to this feature are
resolved; none remain as `NEEDS CLARIFICATION`.

## Phase 1: Design and Contracts

Design outputs:

- [data-model.md](./data-model.md) — the local `Employee.synced` addition,
  the new cloud tables (`synced_employees`, `synced_verification_attempts`,
  `synced_attendance_events`, `corrections`, `cloud_users`,
  `sync_ingest_log`), validation rules, and the computed (non-persisted)
  `Report` view model.
- [contracts/cloud-api.yaml](./contracts/cloud-api.yaml) — the full cloud
  API: auth, the sync ingestion endpoint (site-key authenticated, distinct
  from user JWTs), employees/attendance-history browsing, corrections
  (create + audit-trail read), reports (daily/weekly/monthly/custom +
  export), and user management (Owner-only).
- [quickstart.md](./quickstart.md) — four end-to-end validation scenarios
  (one per user story) plus edge-case checks (cloud outage, force-deleted
  employee with synced history, not-yet-synced report period).

### Post-Design Constitution Check

- **Local-first recording**: PASS. `data-model.md` confirms the only local
  schema change is a single additive column; no local write path or
  behavior changes.
- **Auditability**: PASS. `data-model.md`'s `corrections` table is
  append-only by construction (no update/delete endpoint exists in
  `contracts/cloud-api.yaml`), and `GET /attendance/corrections/{employee_id}`
  exposes the full ordered history, not just the latest value.
- **RBAC/data protection**: PASS. Every write/read endpoint in
  `contracts/cloud-api.yaml` is annotated with which roles may call it; the
  sync ingestion endpoint uses a wholly separate credential type
  (`syncApiKey`) so it can never be reached with a dashboard user's or a
  Guard's JWT. No schema anywhere stores a facial embedding.
- **Guard simplicity / contract-first UI**: PASS. `contracts/cloud-api.yaml`
  is complete enough for `cloud-dashboard/` to be built entirely against
  MSW-mocked responses before `cloud-backend/` exists, matching Feature
  002's proven workflow. The guard's own experience is untouched.
- **Testable delivery**: PASS. `quickstart.md` provides one independently
  runnable scenario per user story (P1–P4) plus three edge-case checks,
  and `data-model.md`'s validation rules are concrete enough to drive
  contract tests directly from `contracts/cloud-api.yaml`.

## Complexity Tracking

Not applicable — no constitution violations were identified.

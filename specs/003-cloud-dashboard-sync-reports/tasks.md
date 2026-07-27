# Tasks: Cloud Dashboard, Sync, and Reports

**Input**: Design documents from `/specs/003-cloud-dashboard-sync-reports/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cloud-api.yaml, quickstart.md

**Tests**: Included, matching how Features 001 and 002 were implemented in this repository — tests are written per user story, never require a live deployment, and integration tests use SQLite (cloud-backend) or MSW (cloud-dashboard) exactly as the existing `backend/`/`frontend/` test suites already do.

**Organization**: Tasks are grouped by user story (P1–P4 from spec.md) so each story is independently implementable, testable, and demoable. Two new projects are introduced (`cloud-backend/`, `cloud-dashboard/`); `backend/` (Feature 001) receives only a small, additive change (one column, one new `sync/` module); `frontend/` (Feature 002) is untouched.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies)
- **[Story]**: US1 (sync), US2 (reports), US3 (corrections), US4 (RBAC/user management)
- Every task names an exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Scaffold both new projects and stage the one local-PC schema change this feature needs.

- [X] T001 Create `cloud-backend/` directory structure (`src/cloud_attendance/{models,schemas,services,api,auth,templates}`, `tests/{unit,integration,contract}`) per plan.md
- [X] T002 Create `cloud-backend/pyproject.toml` with FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2 + pydantic-settings, PyJWT, bcrypt, `psycopg[binary]`, Jinja2, WeasyPrint, `openpyxl` dependencies and `pytest`/`httpx` dev dependencies, mirroring `backend/pyproject.toml`'s conventions (`requires-python = ">=3.11"`, `[tool.pytest.ini_options] pythonpath = ["src"]`)
- [X] T003 [P] Initialize `cloud-backend/alembic/` and `cloud-backend/alembic.ini`, pointed at `cloud_attendance.models.Base.metadata`, mirroring `backend/alembic/`
- [X] T004 [P] Create `cloud-dashboard/` directory structure (`src/{api,auth,components,pages,styles}`, `tests/{unit,integration,msw}`) per plan.md
- [X] T005 [P] Create `cloud-dashboard/package.json` with React 18, Vite, TypeScript, React Router, Vitest, React Testing Library, MSW dependencies and `openapi-typescript` dev dependency; create `cloud-dashboard/tsconfig.json` and `cloud-dashboard/index.html`, mirroring `frontend/`
- [X] T006 [P] Create `cloud-dashboard/vite.config.ts`, `cloud-dashboard/vitest.config.ts`, and `cloud-dashboard/tests/setup.ts` for the Vitest + React Testing Library + jsdom environment
- [X] T007 [P] Create `cloud-dashboard/tests/msw/server.ts` with the base Mock Service Worker setup (empty handlers array)
- [X] T008 [P] Generate TypeScript types from `specs/003-cloud-dashboard-sync-reports/contracts/cloud-api.yaml` into `cloud-dashboard/src/api/types.ts` via `openapi-typescript`, with a `generate:api-types` script added to `cloud-dashboard/package.json`
- [X] T009 [P] Add `synced: Mapped[bool]` column (default `False`) to `Employee` in `backend/src/local_attendance/models/employee.py`, mirroring the existing `VerificationAttempt.synced`/`AttendanceEvent.synced` pattern
- [X] T010 Create the Alembic migration adding the `employees.synced` column in `backend/alembic/versions/` (depends on T009)

**Checkpoint**: Both new projects build and run their (empty) test suites; the local PC schema is ready for a sync job to read/write `synced` flags on all three entities.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cloud auth (login + RBAC dependencies) and the dashboard's session/API-client base — every user story needs an authenticated Owner/Admin/Viewer session, and RBAC must exist before any protected endpoint is written.

**CRITICAL**: No user story work should begin until this phase is complete.

- [X] T011 Create `cloud_attendance/models/__init__.py` (`Base`, `TimestampMixin`, `generate_uuid`, `utcnow`) mirroring `local_attendance/models/__init__.py`
- [X] T012 Create `cloud_attendance/config.py` (`Settings`: `database_url`, `jwt_secret`, `jwt_algorithm`, `access_token_expire_minutes`, and a `sync_api_keys` mapping of `site_key_id` → shared secret, per research.md §6)
- [X] T013 Create `cloud_attendance/database.py` (portable engine/session factory: SQLite `connect_args={"check_same_thread": False}` only when the URL is SQLite, else `{}` — mirrors `backend/src/local_attendance/database.py`)
- [X] T014 [P] Create `cloud_attendance/models/cloud_user.py` (`CloudUser`: `id`, `email` unique, `password_hash`, `role` enum `owner|admin|viewer`, `active`, `invited_by`)
- [X] T015 [P] Create `cloud_attendance/auth/password.py` (`hash_password`/`verify_password`), mirroring `local_attendance/auth/password.py`
- [X] T016 [P] Create `cloud_attendance/auth/tokens.py` (`create_access_token`/`decode_access_token`), mirroring `local_attendance/auth/tokens.py`
- [X] T017 Create `cloud_attendance/auth/dependencies.py` (`get_current_cloud_user`, `require_owner`, `require_admin_or_owner`, `require_any_cloud_role`, `require_sync_api_key`; any decoded role outside `owner|admin|viewer` — including `guard` — is rejected by every cloud-role dependency, per spec FR-023) (depends on T014, T016)
- [X] T018 Create `cloud_attendance/schemas/auth.py` (`LoginRequest`, `LoginResponse`, `CloudUser` schema per `contracts/cloud-api.yaml`)
- [X] T019 Create `cloud_attendance/api/auth.py` (`POST /auth/login`, using the same constant-time dummy-password-hash pattern as `local_attendance/api/auth.py` to avoid username-enumeration timing) (depends on T015, T016, T018)
- [X] T020 Create `cloud_attendance/main.py` (app factory, logging config mirroring `local_attendance/main.py`, router registration, CORS configured for the `cloud-dashboard/` origin)
- [X] T021 Create the initial Alembic migration for the `cloud_users` table in `cloud-backend/alembic/versions/` (depends on T014)
- [X] T022 Create a bootstrap-owner script `cloud-backend/scripts/create_owner.py` (creates the first `CloudUser` with role `owner`, since `POST /users` itself requires an existing Owner to call it)
- [X] T023 [P] Unit tests for password hashing and token create/decode in `cloud-backend/tests/unit/test_auth_tokens.py`
- [X] T024 [P] Integration tests for `POST /auth/login` — success, invalid credentials, inactive/revoked account, and a Guard-role JWT (crafted with `local_attendance`'s own token signer using a shared test secret) being rejected — in `cloud-backend/tests/integration/test_auth.py`
- [X] T025 Create `cloud-dashboard/src/api/client.ts` (typed fetch wrapper: auth header injection, JSON parsing, 401/403/network-error normalization), mirroring `frontend/src/api/client.ts`
- [X] T026 [P] Create `cloud-dashboard/src/api/auth.ts` (`POST /auth/login`)
- [X] T027 [P] Create `cloud-dashboard/src/auth/SessionContext.tsx` (token + role in memory/`sessionStorage`, login/logout, auto-logout on 401), mirroring `frontend/src/auth/SessionContext.tsx`
- [X] T028 [P] Create `cloud-dashboard/src/routes.tsx` (login, overview, employees, employee-history, reports, users routes; role-gated route guarding — Owner-only for the users route)
- [X] T029 [P] Create `cloud-dashboard/src/pages/LoginPage.tsx`
- [X] T030 [P] Create `cloud-dashboard/tests/msw/handlers/auth.ts` (login success/401 handlers)
- [X] T031 [P] Unit test for `SessionContext` in `cloud-dashboard/tests/unit/SessionContext.test.tsx`
- [X] T032 [P] Integration test for `LoginPage` in `cloud-dashboard/tests/integration/LoginPage.test.tsx`
- [X] T033 Add `sync_target_url`, `sync_api_key`, `sync_interval_seconds` settings to `backend/src/local_attendance/config.py`

**Checkpoint**: Owner/Admin/Viewer can log into the cloud dashboard against a running `cloud-backend/`; RBAC dependencies exist and already reject unknown/Guard roles; the local PC has the settings a sync job will need. User story work can now begin.

---

## Phase 3: User Story 1 - See Synced Attendance Data in the Cloud (Priority: P1) 🎯 MVP

**Goal**: Attendance events, verification attempts, and employee metadata recorded on the local PC reach the cloud dashboard reliably, idempotently, and survive connectivity gaps, without ever requiring the cloud for the local guard workflow to keep working.

**Independent Test**: Record attendance on the local PC (some while its sync target is unreachable), restore connectivity, and confirm every event appears exactly once in the cloud dashboard's employee list/history, matching employee, type, timestamp, and outcome — per quickstart.md Scenario 1.

### Tests for User Story 1

- [x] T034 [P] [US1] Contract test for `POST /sync/batch` (valid batch accepted, invalid/missing site key → 401, malformed payload → 422) in `cloud-backend/tests/contract/test_sync_batch_contract.py`
- [x] T035 [P] [US1] Integration test: re-pushing the same batch (retry of an already-delivered batch) does not duplicate any row in `cloud-backend/tests/integration/test_sync_idempotency.py`
- [x] T036 [P] [US1] Integration test: employee metadata sync updates `SyncedEmployee` fields correctly and never accepts or stores a facial embedding field in `cloud-backend/tests/integration/test_sync_employee_metadata.py`
- [x] T037 [P] [US1] Unit test for the local sync client — batches only `synced=false` rows, and marks them `synced=true` only after a 2xx response — in `backend/tests/unit/test_sync_client.py`
- [x] T038 [P] [US1] Integration test simulating an offline gap: events recorded while the sync target is unreachable are still delivered exactly once after connectivity returns, using a fake/failing HTTP transport, in `backend/tests/integration/test_sync_offline_recovery.py`

### Implementation for User Story 1

- [x] T039 [P] [US1] Create `cloud_attendance/models/synced_employee.py` (`SyncedEmployee`, id reused verbatim from the local `Employee.id`)
- [x] T040 [P] [US1] Create `cloud_attendance/models/synced_verification_attempt.py` (`SyncedVerificationAttempt`)
- [x] T041 [P] [US1] Create `cloud_attendance/models/synced_attendance_event.py` (`SyncedAttendanceEvent`)
- [x] T042 [P] [US1] Create `cloud_attendance/models/sync_ingest_log.py` (`SyncIngestLog`)
- [x] T043 [US1] Create the Alembic migration for `synced_employees`, `synced_verification_attempts`, `synced_attendance_events`, and `sync_ingest_log` in `cloud-backend/alembic/versions/` (depends on T039–T042)
- [x] T044 [P] [US1] Create `cloud_attendance/schemas/sync.py` (`SyncBatchRequest`/`SyncBatchResponse` per `contracts/cloud-api.yaml`)
- [x] T045 [US1] Implement `cloud_attendance/services/sync_ingest_service.py` (upsert-by-id: an id that already exists is a no-op still counted as accepted; a new id is inserted) (depends on T039–T042)
- [x] T046 [US1] Implement `cloud_attendance/api/sync.py` (`POST /sync/batch`, gated by `require_sync_api_key`) (depends on T044, T045, T017)
- [x] T047 [P] [US1] Implement `backend/src/local_attendance/sync/client.py` (httpx push of `synced=false` `Employee`/`VerificationAttempt`/`AttendanceEvent` rows in batches; flips `synced=true` locally only on a 2xx response; capped exponential backoff on failure)
- [x] T048 [US1] Implement `backend/src/local_attendance/sync/scheduler.py` (in-process `asyncio` background loop reading `sync_interval_seconds`, invoking `sync/client.py` each tick) (depends on T047)
- [x] T049 [US1] Wire the sync scheduler's startup/shutdown into `backend/src/local_attendance/main.py`'s FastAPI lifespan (depends on T048)
- [x] T050 [P] [US1] Create `cloud-dashboard/src/api/employees.ts` (`GET /employees`)
- [x] T051 [P] [US1] Create `cloud-dashboard/src/pages/EmployeeListPage.tsx` (browse synced employees, search/filter by name/department/active)
- [x] T052 [P] [US1] Create `cloud-dashboard/tests/msw/handlers/employees.ts` (employee-list fixtures)
- [x] T053 [P] [US1] Integration test for `EmployeeListPage` in `cloud-dashboard/tests/integration/EmployeeListPage.test.tsx`

**Checkpoint**: Local attendance data syncs to the cloud reliably and idempotently, survives offline gaps, and Owner/Admin/Viewer can browse the synced employee list in the cloud dashboard. This is the deployable MVP.

---

## Phase 4: User Story 2 - Generate and Export Attendance Reports (Priority: P2)

**Goal**: Owner/Admin/Viewer can generate daily/weekly/monthly organization-wide reports or a custom per-employee report, and export/print them with all client-required fields.

**Independent Test**: Generate a report against known synced data, confirm the on-screen result, the PDF export, and the Excel export all match — per quickstart.md Scenario 2.

### Tests for User Story 2

- [x] T054 [P] [US2] Contract tests for `GET /reports/daily`, `/weekly`, `/monthly`, `/custom` in `cloud-backend/tests/contract/test_reports_contract.py`
- [x] T055 [P] [US2] Contract test for `GET /reports/export` with `format=pdf` and `format=xlsx` in `cloud-backend/tests/contract/test_reports_export_contract.py`
- [x] T056 [P] [US2] Integration test: an unmatched arrival/departure pair is flagged with the correct `completeness` value, and `may_be_incomplete` is true when the requested period extends past the most recent successful sync, in `cloud-backend/tests/integration/test_report_completeness.py`
- [x] T057 [P] [US2] Integration test: the PDF export contains company name, period, the arrival/departure table, a missing-record note, generation date, and a signature area, in `cloud-backend/tests/integration/test_report_pdf_export.py`
- [x] T058 [P] [US2] Integration test: the Excel export's rows match the on-screen report exactly, in `cloud-backend/tests/integration/test_report_excel_export.py`
- [x] T059 [P] [US2] Integration test: a Viewer can generate/export/print reports but sees no data-modifying control anywhere on `ReportsPage`, in `cloud-dashboard/tests/integration/ReportsPage.viewer.test.tsx`

### Implementation for User Story 2

- [x] T060 [US2] Implement `cloud_attendance/services/report_service.py` (daily/weekly/monthly/custom aggregation, arrival/departure pairing per employee-day, completeness classification, `may_be_incomplete` flag) (depends on T039–T041)
- [x] T061 [P] [US2] Create `cloud_attendance/templates/report.html.jinja` (shared HTML/CSS: company name, employee/period header, arrival/departure table, missing-records note, generation date, signature area)
- [x] T062 [US2] Implement `cloud_attendance/services/export_service.py` (WeasyPrint PDF render from `report.html.jinja`; `openpyxl` workbook builder with one row per employee-day) (depends on T060, T061)
- [x] T063 [P] [US2] Create `cloud_attendance/schemas/report.py` (`ReportRow`, `Report` per `contracts/cloud-api.yaml`)
- [x] T064 [US2] Implement `cloud_attendance/api/reports.py` (`GET /reports/daily|weekly|monthly|custom|export`, gated by `require_any_cloud_role`) (depends on T060, T062, T063, T017)
- [x] T065 [P] [US2] Create `cloud-dashboard/src/api/reports.ts` (report fetch + PDF/Excel download calls)
- [x] T066 [P] [US2] Create `cloud-dashboard/src/components/ReportTable.tsx` and `cloud-dashboard/src/components/CompletenessBadge.tsx`
- [x] T067 [US2] Create `cloud-dashboard/src/pages/ReportsPage.tsx` (period/scope selectors, on-screen report, export PDF/Excel buttons, print) (depends on T065, T066)
- [x] T068 [P] [US2] Create `cloud-dashboard/tests/msw/handlers/reports.ts` (fixtures for daily/weekly/monthly/custom + export)

**Checkpoint**: Reports generate, export, and print correctly for Owner/Admin/Viewer, with incomplete-data periods clearly flagged.

---

## Phase 5: User Story 3 - Correct Missing or Wrong Attendance Records (Priority: P3)

**Goal**: Owner/Admin can add or correct attendance records with a required reason, non-destructively, with a full audit trail — never touching the local PC's own data.

**Independent Test**: Create a correction against a synced event; confirm the original is preserved, the correction is fully traceable, and reports reflect the corrected value — per quickstart.md Scenario 3.

### Tests for User Story 3

- [x] T069 [P] [US3] Contract test for `POST /attendance/corrections` — missing reason → 400, `add_arrival`/`add_departure` with an `attendance_event_id` (or `correct_time`/`change_type` without one) → 400, Viewer → 403 — in `cloud-backend/tests/contract/test_corrections_contract.py`
- [x] T070 [P] [US3] Contract test for `GET /attendance/corrections/{employee_id}` — ordered audit trail, Viewer → 403 — in `cloud-backend/tests/contract/test_corrections_audit_contract.py`
- [x] T071 [P] [US3] Integration test: creating a correction leaves the original `synced_attendance_events` row unchanged, while reports/history reflect the corrected value, in `cloud-backend/tests/integration/test_correction_non_destructive.py`
- [x] T072 [P] [US3] Integration test: two corrections to the same event both appear in the audit trail, in order, in `cloud-backend/tests/integration/test_correction_chain.py`
- [x] T073 [P] [US3] Integration test confirming a cloud correction never writes to or otherwise touches the local PC's SQLite database, in `cloud-backend/tests/integration/test_correction_local_pc_unaffected.py`
- [x] T074 [P] [US3] Integration test for the `EmployeeHistoryPage` correction flow (add missing departure, edit a timestamp, view audit trail) in `cloud-dashboard/tests/integration/EmployeeHistoryPage.correction.test.tsx`

### Implementation for User Story 3

- [x] T075 [P] [US3] Create `cloud_attendance/models/correction.py` (`Correction`: `action` enum `add_arrival|add_departure|correct_time|change_type`, `previous_value`/`new_value` as JSON text, `reason`, `performed_by`, `performed_at` — append-only by construction, no update/delete path)
- [x] T076 [US3] Create the Alembic migration for the `corrections` table in `cloud-backend/alembic/versions/` (depends on T075)
- [x] T077 [P] [US3] Create `cloud_attendance/schemas/correction.py` (`CorrectionCreate`, `Correction` per `contracts/cloud-api.yaml`)
- [x] T078 [US3] Implement `cloud_attendance/services/correction_service.py` (enforces: `reason` non-empty; `add_arrival`/`add_departure` MUST NOT reference an existing `attendance_event_id`; `correct_time`/`change_type` MUST; writes are append-only) (depends on T075, T077)
- [x] T079 [US3] Implement `cloud_attendance/api/corrections.py` (`POST /attendance/corrections` and `GET /attendance/corrections/{employee_id}`, both gated by `require_admin_or_owner`) (depends on T078, T017)
- [x] T080 [US3] Update `cloud_attendance/services/report_service.py` to apply the latest correction per attendance-event on top of synced data, setting `corrected=true` on affected rows (depends on T060, T078)
- [x] T081 [US3] Implement `cloud_attendance/api/employees.py`'s `GET /employees/{employee_id}/attendance` (date-by-date history combining synced events with corrections) (depends on T078)
- [x] T082 [P] [US3] Create `cloud-dashboard/src/api/corrections.ts`
- [x] T083 [P] [US3] Create `cloud-dashboard/src/components/AuditTrailList.tsx`
- [x] T084 [US3] Create `cloud-dashboard/src/pages/EmployeeHistoryPage.tsx` (date-by-date history, correction form and audit trail visible only to Owner/Admin) (depends on T082, T083)
- [x] T085 [P] [US3] Create `cloud-dashboard/tests/msw/handlers/corrections.ts`

**Checkpoint**: Owner/Admin can non-destructively correct attendance data with a complete audit trail; Viewer cannot; the local PC's own records are provably unaffected.

---

## Phase 6: User Story 4 - Enforce Roles Across the Cloud Dashboard (Priority: P4)

**Goal**: An Owner manages cloud user accounts and roles (Owner/Admin/Viewer only); every cloud endpoint enforces roles server-side, and Guard-role tokens are rejected everywhere.

**Independent Test**: Invite an Admin, confirm their access, change their role, revoke them, and confirm a Guard JWT is rejected by every dashboard-only endpoint — per quickstart.md Scenario 4.

### Tests for User Story 4

- [x] T086 [P] [US4] Contract test for `GET`/`POST /users` (Owner only; non-Owner → 403) in `cloud-backend/tests/contract/test_users_contract.py`
- [x] T087 [P] [US4] Contract test for `PATCH /users/{user_id}` (role change, revoke via `active: false`, rejecting an attempt to set `role: guard`) in `cloud-backend/tests/contract/test_users_update_contract.py`
- [x] T088 [P] [US4] Integration test: a revoked user is denied on their very next authenticated action (not just at their next login) in `cloud-backend/tests/integration/test_user_revocation.py`
- [x] T089 [P] [US4] Integration test: every dashboard-only endpoint (`/employees`, `/attendance/corrections*`, `/reports/*`, `/users*`) rejects a valid local-PC Guard JWT, in `cloud-backend/tests/integration/test_guard_role_rejected_everywhere.py`
- [x] T090 [P] [US4] Integration test for `UserManagementPage` (invite, change role, revoke) in `cloud-dashboard/tests/integration/UserManagementPage.test.tsx`

### Implementation for User Story 4

- [x] T091 [US4] Implement `cloud_attendance/services/user_service.py` (invite, change role, revoke; rejects `role="guard"` at the service layer, not just the schema) (depends on T014)
- [x] T092 [US4] Implement `cloud_attendance/api/users.py` (`GET`/`POST /users`, `PATCH /users/{user_id}`, gated by `require_owner`) (depends on T091, T017)
- [x] T093 [P] [US4] Create `cloud-dashboard/src/api/users.ts`
- [x] T094 [US4] Create `cloud-dashboard/src/pages/UserManagementPage.tsx` (Owner-only route: invite form, role/active editing) (depends on T093)
- [x] T095 [P] [US4] Create `cloud-dashboard/tests/msw/handlers/users.ts`

**Checkpoint**: All four user stories are independently functional; RBAC is enforced backend-side end-to-end, including provable Guard rejection.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T096 [P] Create `cloud-backend/README.md` (setup, running migrations, running tests, the bootstrap-owner script, required environment variables)
- [x] T097 [P] Create `cloud-dashboard/README.md` (setup, running tests, MSW dev mode, generating API types)
- [x] T098 [P] Add a `cloud-backend/Dockerfile` (or equivalent deploy config for Render/Railway per `docs/plan_pointage_facial.md` §5 — the specific provider remains a deployment-time choice, not fixed here)
- [x] T099 [P] Add `cloud-dashboard` static-build deploy config with an env-configured cloud API base URL
- [x] T100 Update `backend/README.md` documenting the new `sync/` module, its settings, and how to point it at a cloud deployment
- [x] T101 Execute quickstart.md end-to-end (all 4 scenarios + the three edge-case checks) against a real or staging deployment and record the results
- [x] T102 Review `.specify/memory/constitution.md` against the completed implementation to confirm no further amendment is needed (corrections/audit trail requirements are now finally implemented, closing the gap Feature 001/002 explicitly deferred)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks all user stories — every story needs cloud login + RBAC.
- **User Stories (Phase 3–6)**: All depend on Foundational completion.
  - **US1 (sync)** has no dependency on US2–US4 and should be built first — every other story needs synced data to operate on.
  - **US2 (reports)** and **US3 (corrections)** both depend on US1's synced data existing, but not on each other.
  - **US4 (RBAC/user management)** depends only on Foundational (the RBAC dependencies already exist there); it can technically be built in parallel with US2/US3, but its own tests (T089) are most meaningful once US1–US3's endpoints exist to attempt against.
- **Polish (Phase 7)**: Depends on all four user stories being complete.

### Within Each User Story

- Tests are listed first and MUST fail before their corresponding implementation task is done.
- Models before services; services before API endpoints; backend endpoints before the dashboard pages that call them.

### Parallel Opportunities

- All `[P]` Setup tasks (T003, T004–T009) can run together.
- Within Foundational, cloud-backend tasks (T011–T024) and cloud-dashboard tasks (T025–T032) can proceed in parallel once T011–T020 establish the API shape both sides code against (`contracts/cloud-api.yaml` already fixes that shape, so cloud-dashboard work does not actually need to wait).
- Within each user story, all model-creation tasks marked `[P]` can run together, as can all `[P]` test tasks.
- US2, US3, and US4 can be staffed in parallel by different contributors once US1 is done, since none of them depend on each other's implementation — only on US1's synced data existing.

---

## Parallel Example: User Story 1

```bash
# Tests for User Story 1 (run together):
Task: "Contract test for POST /sync/batch in cloud-backend/tests/contract/test_sync_batch_contract.py"
Task: "Integration test: idempotent re-push in cloud-backend/tests/integration/test_sync_idempotency.py"
Task: "Unit test for local sync client in backend/tests/unit/test_sync_client.py"
Task: "Integration test: offline gap recovery in backend/tests/integration/test_sync_offline_recovery.py"

# Models for User Story 1 (run together):
Task: "Create SyncedEmployee model in cloud_attendance/models/synced_employee.py"
Task: "Create SyncedVerificationAttempt model in cloud_attendance/models/synced_verification_attempt.py"
Task: "Create SyncedAttendanceEvent model in cloud_attendance/models/synced_attendance_event.py"
Task: "Create SyncIngestLog model in cloud_attendance/models/sync_ingest_log.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (blocks everything else)
3. Complete Phase 3: User Story 1 (sync + employee browsing)
4. **STOP and VALIDATE**: run quickstart.md Scenario 1 end-to-end
5. Deploy/demo if ready — this alone proves the cloud pipeline works

### Incremental Delivery

1. Setup + Foundational → cloud login and RBAC work
2. + User Story 1 → sync works, employees browsable (MVP)
3. + User Story 2 → reports generate and export
4. + User Story 3 → corrections with audit trail
5. + User Story 4 → full multi-user role management
6. + Polish → documentation, deploy config, quickstart sign-off

### Parallel Team Strategy

1. Everyone completes Setup + Foundational together (this is the one phase that genuinely blocks all others).
2. One contributor takes US1 first (it unblocks US2/US3 with real data to work against).
3. Once US1's cloud-side models/ingestion exist, US2, US3, and US4 can be split across contributors in parallel — each is independently testable against the same `contracts/cloud-api.yaml`.
4. Polish tasks are picked up as each story completes its own checkpoint.

---

## Notes

- `[P]` tasks touch different files with no unmet dependency — safe to parallelize.
- `[Story]` labels trace every task back to spec.md's US1–US4 for independent delivery.
- Guard accounts never receive a `cloud_users` row (per the resolved spec clarification, FR-023) — T089 exists specifically to prove the backend still actively rejects a Guard JWT rather than merely never issuing one.
- Corrections are append-only by construction (T075): no task in this list ever adds an update/delete endpoint for `corrections`, by design.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently before moving on.

# Cloud Attendance (Backend)

Cloud-side management service for the facial attendance system: receives the
local PC's one-way sync push, and serves the management dashboard's
authenticated Owner/Admin/Viewer users — employee browsing, attendance
history, non-destructive manual corrections with a full audit trail, and
daily/weekly/monthly/custom reports with PDF/Excel export. See
`specs/003-cloud-dashboard-sync-reports/` for the full feature spec.

The local PC (`backend/`, Feature 001) remains the sole source of truth for
raw attendance data; this service never writes back to it. Guard accounts
have no access here at all — a Guard-role token is recognized only so it can
be explicitly rejected (spec FR-023).

## Setup

```bash
cd cloud-backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # adjust values, especially CLOUD_ATTENDANCE_JWT_SECRET
alembic upgrade head
python scripts/create_owner.py owner@example.com <choose-a-password>
uvicorn cloud_attendance.main:app --reload --port 8001
```

There is no public sign-up endpoint by design (spec Assumptions: "no public
self-service sign-up"). `scripts/create_owner.py` creates the first Owner
account; every subsequent cloud user is invited through that Owner via
`POST /users` (Owner-only).

The API is served at `http://localhost:8001` by default (port 8001, distinct
from the local PC's `backend/` on port 8000, so both can run side by side in
development) and matches
`specs/003-cloud-dashboard-sync-reports/contracts/cloud-api.yaml`. Open
`http://localhost:8001/docs` for interactive Swagger UI.

In production, `CLOUD_ATTENDANCE_DATABASE_URL` should point at a real
PostgreSQL instance (`psycopg[binary]` is already a dependency); SQLite is
the development/test default only. All models use portable SQLAlchemy column
types (`String(36)` UUIDs, `Enum(..., native_enum=False)`,
`DateTime(timezone=True)`) so the same schema and migrations work unchanged
against both engines (research.md §7).

## Sync ingestion

The local PC's sync job (`backend/src/local_attendance/sync/`) authenticates
to `POST /sync/batch` with a per-site API key (`X-Sync-Api-Key` header), not
a user JWT — this is a machine-to-machine credential, configured identically
on both sides (`CLOUD_ATTENDANCE_SYNC_API_KEYS` here,
`LOCAL_ATTENDANCE_SYNC_API_KEY` on the local PC). See research.md §6 for why
this is a separate credential type from dashboard logins.

## Migrations

```bash
alembic upgrade head          # apply all migrations
alembic revision --autogenerate -m "description"
```

Migrations create, in order: `cloud_users`; `synced_employees` /
`synced_verification_attempts` / `synced_attendance_events` /
`sync_ingest_logs`; `corrections`.

## Tests

```bash
pytest
pytest tests/contract
pytest tests/integration
pytest tests/unit
```

Tests run against an in-memory SQLite database (see `tests/conftest.py`) —
no PostgreSQL, no local PC, and no network access required. `owner_user` /
`admin_user` / `viewer_user` fixtures (plus their matching `*_auth_headers`)
cover the three real cloud roles; Guard-role rejection is tested by minting a
`role="guard"` JWT directly with `create_access_token` (mirroring what the
local PC's own token signer would produce), since Guard accounts never exist
in `cloud_users` at all.

## Quickstart validation

The scenarios in `specs/003-cloud-dashboard-sync-reports/quickstart.md` are
covered by the automated suite:

| Scenario | Covered by |
| --- | --- |
| 1. Sync survives an offline gap | `cloud-backend/tests/integration/test_sync_idempotency.py`, `test_sync_employee_metadata.py`; `backend/tests/integration/test_sync_offline_recovery.py`, `backend/tests/unit/test_sync_client.py` |
| 2. Generate and export reports | `tests/contract/test_reports_contract.py`, `test_reports_export_contract.py`; `tests/integration/test_report_completeness.py`, `test_report_pdf_export.py`, `test_report_excel_export.py` |
| 3. Manual correction with audit trail | `tests/contract/test_corrections_contract.py`, `test_corrections_audit_contract.py`; `tests/integration/test_correction_non_destructive.py`, `test_correction_chain.py`, `test_correction_local_pc_unaffected.py` |
| 4. RBAC enforcement, including Guard rejection | `tests/contract/test_users_contract.py`, `test_users_update_contract.py`; `tests/integration/test_user_revocation.py`, `test_guard_role_rejected_everywhere.py` |
| Edge case: cloud unreachable doesn't block local guard flow | Inherent — `backend/`'s guard workflow has no runtime dependency on this service; see `backend/tests/` (Feature 001/002 suites, unaffected by this feature) |
| Edge case: report on a not-yet-synced period | `tests/integration/test_report_completeness.py::test_report_may_be_incomplete` |

**Live cross-process validation performed**: beyond the mocked test suites
above, `backend/`'s real `sync/client.py` was run against a genuinely
separate, live `cloud-backend/` process (real `uvicorn`, real migrated
SQLite, real HTTP over `127.0.0.1`, real bcrypt/JWT login) to confirm the two
independently-developed sides of the sync contract actually interoperate:
creating an employee locally and syncing it landed correctly in the cloud
via `GET /employees`; then editing that employee locally (department change
+ deactivation) and syncing again correctly *updated* the same cloud row
(same id, new `synced_at` stamped by the cloud, not the client) rather than
being silently dropped or duplicated — this specifically exercises the
upsert/dirty-tracking fix described in this feature's implementation notes.

**Not yet validated**: a real deployment (Render/Railway) against a real
PostgreSQL instance, and a run across two genuinely separate physical
machines rather than two local processes. The mocked test suites plus the
live cross-process check above cover the logic thoroughly; they do not
substitute for one full rehearsal on the actual target infrastructure before
go-live.

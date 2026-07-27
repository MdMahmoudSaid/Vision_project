# Research: Cloud Dashboard, Sync, and Reports

All items below were previously open (or newly raised by this feature) and
are now resolved. None remain marked `NEEDS CLARIFICATION` in `plan.md`.

## 1. Cloud backend stack and package layout

**Decision**: A new, separate Python package `cloud_attendance` under a new
top-level `cloud-backend/` directory, mirroring `backend/`'s existing
structure exactly (FastAPI, SQLAlchemy 2.x, Alembic, pydantic v2 +
pydantic-settings, PyJWT, bcrypt), with its own `pyproject.toml`, `alembic/`,
`src/cloud_attendance/{models,schemas,services,api,auth,reports}`, and
`tests/{unit,integration,contract}`.

**Rationale**: `docs/plan_pointage_facial.md` §5 explicitly calls for "même
stack que le local, réutilisable" — the cloud backend reuses the same
architectural patterns (JWT-with-role-in-token, `require_*` FastAPI
dependencies for RBAC, service-layer functions returning plain dataclasses
that API routers translate to Pydantic schemas) already proven in
`backend/src/local_attendance`. A separate package (not a shared library)
keeps the two backends independently deployable, matching the constitution's
requirement that the cloud backend never becomes required for local
operation — a shared codebase or shared runtime would blur that boundary.

**Alternatives considered**: A single monorepo Python package shared between
local and cloud was rejected — the two backends have different databases,
different auth realities (human login locally and in the cloud vs. a
machine credential for sync), and different deployment targets; forcing a
shared package would need conditional logic and packaging complexity for no
real benefit, since there is very little code that both actually need beyond
patterns (which can simply be copied, as Feature 001/002 already did for
JWT/RBAC conventions rather than sharing a library).

## 2. Cloud dashboard frontend stack

**Decision**: A new top-level `cloud-dashboard/` directory: React 18 + Vite +
TypeScript, React Router, Vitest + React Testing Library + MSW for tests —
identical tooling to `frontend/` (Feature 002), consuming a new
`contracts/cloud-api.yaml`.

**Rationale**: Consistency with the existing frontend stack lets the same
contributor (or the next intern) work on both without context-switching
tooling; MSW-mocked contract-first development is already the established
pattern from Feature 002 and satisfies the constitution's "Guard-First
Simplicity and Contract-First UI" principle (frontend work starts from a
frozen contract with mock responses).

**Alternatives considered**: A server-rendered framework (Next.js) was
considered for report-heavy pages, but rejected — it would introduce a
second frontend toolchain into the repo for marginal benefit, since reports
are generated server-side (PDF/Excel) and the dashboard itself is a
typical authenticated SPA, exactly what Vite + React already serves well.

## 3. Sync transport, direction, and idempotency

**Decision**: One-way push, local PC → cloud, over HTTPS, using each local
record's existing UUID primary key as the cloud's primary key too (an
upsert: if a row with that ID already exists in the cloud, the push is a
no-op; the response still reports success). The local PC batches records
where `synced = false` (already a column on `VerificationAttempt` and
`AttendanceEvent` in `backend/src/local_attendance/models`), sends them to a
dedicated cloud ingestion endpoint, and only flips `synced = true` locally
after the cloud confirms receipt (2xx). If the confirmation itself is lost
(network drop after the cloud already committed), the next retry re-sends
the same UUIDs; the cloud's upsert-by-ID logic makes this safe.

**Rationale**: This exactly matches the schema that Feature 001 already
shipped in anticipation of this feature (`synced: bool` columns exist
today, unused until now) and the plan document's own stated design ("Sync PC
local → cloud: job périodique simple (push des événements `synced = false`)
... pas de résolution de conflits nécessaire — le PC local est la seule
source qui écrit les données de pointage"). Using the same UUID on both
sides is what makes the sync trivially idempotent without inventing a
separate reconciliation/dedup mechanism.

**Alternatives considered**: A cloud-generated ID with a local→cloud ID
mapping table was rejected as unnecessary complexity — since the local PC
already generates globally-unique UUIDs (`generate_uuid()`), there is no
collision risk in reusing them as the cloud's primary keys directly.
Bidirectional sync (cloud corrections flowing back to the local PC) was
rejected per the plan document's own recommendation and the spec's resolved
assumption (FR-022): the local PC does not need to know about corrections;
the cloud is the system of record for corrected/reported values going
forward.

## 4. Employee metadata sync (no `synced` column yet)

**Decision**: Add a `synced: bool = False` column to the local `Employee`
model (Alembic migration in `backend/`), set to `False` on create/update and
flipped to `True` after a successful push — the exact same pattern already
used for `VerificationAttempt.synced` and `AttendanceEvent.synced`.

**Rationale**: Consistency with the existing two entities' proven pattern
is simpler than introducing a different mechanism (e.g., a generic
watermark/cursor table) for just one more entity. It also makes "what needs
to sync" a single indexed boolean-column query across all three entities,
which the sync job can treat uniformly.

**Alternatives considered**: A single generic `sync_outbox` table (capturing
entity type + entity id + payload snapshot at write time) was considered —
this is a more general "outbox pattern" used in some distributed systems.
Rejected as premature for this project's scale (single guard post, modest
write volume): it would require dual-writing to the outbox on every mutation
across several services, more surface area for bugs, for a benefit (strict
delivery ordering across entity types) this project's data model does not
need — attendance events, verification attempts, and employees can each sync
independently, in any relative order, without breaking data integrity.

## 5. Sync scheduling mechanism

**Decision**: An in-process background task inside the existing local
FastAPI app (`backend/`), started at application startup, looping on a
configurable interval (default 60 seconds) with capped exponential backoff
on failure, using `httpx` as the outbound HTTP client.

**Rationale**: The local PC's FastAPI process is already the thing that must
stay running for the guard workflow to work at all (per the constitution and
Feature 001's existing "keep the service running" operational assumption);
piggy-backing sync on the same process means there is nothing new to install
or keep alive on-site. `httpx` is already a dev-only dependency of
`backend/` (used in tests); this feature promotes it to a runtime dependency
since the sync client is now a real runtime concern, not just test tooling.

**Alternatives considered**: A separate OS-level cron job or scheduled task
was rejected — it would require its own installation/monitoring story on a
Windows or Linux on-site PC that the guard-post staff must maintain, which is
exactly the kind of extra operational surface the constitution's
"local PC = single point of failure, minimize what can go wrong on-site"
risk (`docs/plan_pointage_facial.md` §12) is trying to avoid. A heavier
scheduler library (APScheduler, Celery+broker) was rejected as unnecessary
for a single periodic loop; a plain `asyncio` background task is sufficient
and adds no new dependency.

## 6. Machine-to-machine authentication for the sync push

**Decision**: A single long-lived, site-specific bearer credential (a random
opaque API key, configured once via environment variable on both the local
PC and the cloud backend at deployment time), sent as a bearer token/custom
header on sync requests. This is a distinct concept from the human JWTs used
for Owner/Admin/Viewer dashboard logins and from the local PC's own
guard/admin JWTs — it authenticates "this specific site's sync job," not a
person.

**Rationale**: The sync job is not a human session; it does not need roles,
expiry-driven re-login, or a user record. Inventing a fake "system user" and
issuing it a JWT would add modeling complexity (a user row that never really
logs in, that must be excluded from every "list users" screen) for no
benefit over a plain shared secret scoped to exactly one capability (push
sync batches). If the client ever has multiple guard-post PCs syncing to one
cloud tenant, each gets its own key, so a leaked or rotated key only affects
one site.

**Alternatives considered**: Reusing the human JWT scheme with a dedicated
"sync" role was rejected — it conflates two different trust boundaries
(a person's session vs. a site's standing integration credential) and would
force the cloud's user-management screen (FR-020) to somehow explain why a
"sync" user shows up in the Owner's user list.

## 7. Database portability: PostgreSQL in production, SQLite in tests

**Decision**: Write `cloud_attendance`'s SQLAlchemy models using only
DB-portable column types (`String(36)` UUID primary keys, `Enum(...,
native_enum=False)`, `DateTime(timezone=True)`) — the exact same portable
style `local_attendance`'s models already use. Tests run against an
in-memory/file SQLite database; the deployed cloud backend points
`DATABASE_URL` at a real PostgreSQL instance. No PostgreSQL-only column types
(no native `JSONB`/`ARRAY`) are used, so the same model definitions and
migrations work unchanged against both engines.

**Rationale**: This mirrors `backend/`'s own successful approach exactly (its
tests already run this way against SQLite while nothing in production
requires SQLite specifically) and avoids adding a heavier test
infrastructure dependency (Docker, `testcontainers`, `pytest-postgresql`) to
a project that currently has none. Given this project's modest scale (one
client, one cloud tenant), the small semantic gaps between SQLite and
PostgreSQL are not a practical risk as long as portable types are used
throughout.

**Alternatives considered**: `testcontainers-python` (spins up a real
throwaway PostgreSQL container per test run) was considered for higher test
fidelity. Rejected for now as added CI/local-dev complexity (Docker
dependency) that this project's team size and scale do not justify; can be
revisited later if a genuinely Postgres-only feature (e.g., full-text search)
is ever needed.

## 8. PDF and Excel export libraries

**Decision**: WeasyPrint (HTML/CSS → PDF, rendered from Jinja2 templates) for
PDF export; `openpyxl` for Excel export — both per
`docs/plan_pointage_facial.md` §5's already-confirmed stack choice.

**Rationale**: WeasyPrint lets the report's PDF layout be authored in
HTML/CSS, reusing the same visual design as the on-screen/print view (spec
FR-016's "same print-friendly layout as the PDF export"), and handles
tables/pagination/signature areas well. `openpyxl` is the standard,
dependency-light choice for `.xlsx` generation in Python.

**Alternatives considered**: `reportlab` (lower-level PDF drawing API) was
rejected — it would require building table/pagination layout logic by hand
instead of reusing HTML/CSS, doubling the design work between the on-screen
report and the exported PDF.

## 9. Cloud RBAC dependency shape

**Decision**: Mirror `backend/src/local_attendance/auth/dependencies.py`'s
`require_admin` / `require_guard_or_admin` pattern with cloud-specific
FastAPI dependencies: `require_owner`, `require_admin_or_owner`, and
`require_any_cloud_role` (Owner, Admin, or Viewer — i.e., "any authenticated
cloud user," used for read-only endpoints like report generation). A
Guard-role JWT decodes successfully (same PyJWT/HS256 mechanism) but is
rejected by all three dependencies, satisfying spec FR-023.

**Rationale**: Directly reuses a pattern already proven correct and
constitution-compliant (backend-enforced, not UI-only) in Feature 001,
minimizing new concepts for future maintainers to learn.

**Alternatives considered**: A more general permissions-matrix/policy engine
(e.g., attribute-based access control) was rejected as over-engineering for
three roles and a handful of endpoints; the constitution's own permission
model is already just a small fixed role list per endpoint.

## 10. Correction data model and action taxonomy

**Decision**: A `corrections` table in the cloud database only, with an
`action` enum (`add_arrival`, `add_departure`, `correct_time`,
`change_type`), `previous_value`/`new_value` stored as JSON text (portable
across SQLite/PostgreSQL, same approach as `FacialReference.embedding` being
stored as `Text`), `reason` (required, non-empty), `performed_by` (cloud user
id), `performed_at`, and an optional link to the `attendance_event_id` being
corrected (nullable when adding a missing event rather than editing one).

**Rationale**: This exact taxonomy and shape is already specified in
`docs/plan_pointage_facial.md` §6's data model section for `corrections`;
reusing it verbatim avoids re-deriving a shape the plan already settled.

**Alternatives considered**: Storing corrections as a generic append-only
event log (event-sourcing style, replaying all corrections to derive current
state at read time) was rejected as unnecessary complexity — the volume of
corrections is expected to be low, and a simple "latest correction wins for
display, full history still queryable" model (FR-013) is sufficient and far
simpler to reason about and test.

## 11. Printed/PDF report content fields

**Decision**: Fixed content fields (not a visual mockup) per the cahier de
charge, already adopted into spec FR-014/FR-016: company name, employee
name/number (or "all employees" for organization-wide reports), the period
covered, the arrival/departure table, a note of any missing records, the
report generation date, and a signature area. The pixel-level visual design
(logo placement, exact typography) is treated as a follow-up design task,
not a blocker for this plan.

**Rationale**: The cahier de charge already specifies the required fields
(`docs/plan_pointage_facial.md` line 24); only the visual mockup was left
open, and that is a design/validation activity that does not change the data
or API contract this plan defines.

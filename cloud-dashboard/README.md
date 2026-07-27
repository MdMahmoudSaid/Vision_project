# Cloud Attendance Dashboard

Management dashboard for Owner/Admin/Viewer cloud users: browse synced
employees, review attendance history, add non-destructive corrections with a
full audit trail, and generate/export/print attendance reports. See
`specs/003-cloud-dashboard-sync-reports/` for the full feature spec.

Unlike the local guard PWA (`frontend/`), this is **not** served by its
backend as static assets co-located in one process — `cloud-backend/` and
this dashboard are two independently deployed services, so the dashboard
always calls the cloud API over a real HTTP origin, configured via
`VITE_API_BASE_URL` in production.

Guard accounts have no access to this dashboard at all (spec FR-023,
resolved clarification) — there are no guard-facing screens here; Guards
continue to use only `frontend/`.

## Setup

```bash
cd cloud-dashboard
npm install
npm run generate:api-types   # regenerate src/api/types.ts if the contract changes
```

## Development

`cloud-backend/` must be running on `http://127.0.0.1:8001` (its default dev
port). `vite.config.ts` proxies relative API paths (`/auth`, `/employees`,
`/attendance`, `/reports`, `/users`) to that port, so no `.env` is needed in
dev — `src/api/client.ts`'s `apiUrl()` falls back to relative paths when
`VITE_API_BASE_URL` is unset.

```bash
npm run dev
```

## Tests

```bash
npm test
```

Tests run entirely against Mock Service Worker (`tests/msw/`) — no running
backend required. `tests/msw/handlers/corrections.ts` and `handlers/users.ts`
keep small in-memory stores reset between tests (`resetCorrectionsStore` /
`resetUsersStore` in `tests/setup.ts`) so form-submission flows (create a
correction, invite a user) can be exercised end-to-end within a single test.

## Production build and deployment

```bash
cp .env.example .env   # set VITE_API_BASE_URL to the deployed cloud-backend origin
npm run build           # tsc -b && vite build -> dist/
```

`dist/` is a static site — deploy it to any static host (Render/Railway
static site, or equivalent per `docs/plan_pointage_facial.md` §5). It is a
separate deployable from `cloud-backend/`; there is no shared process or
same-origin assumption between them.

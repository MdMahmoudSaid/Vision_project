# Implementation Plan: Guard PWA Local Interface

**Branch**: `002-guard-pwa-interface` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-guard-pwa-interface/spec.md`

## Summary

Build the guard-facing Progressive Web App that consumes the already-shipped
local attendance API (`specs/001-local-attendance-core/contracts/local-api.yaml`)
over the local Wi-Fi network. The guard logs in, searches/selects an active
employee, chooses arrival or departure, triggers verification, and sees a
clear success/failure/duplicate result — at most three actions after login.
Administrators additionally see employee creation and face enrollment;
guards never see those actions, and the backend independently enforces that
restriction regardless of what the UI shows.

Technical approach: a React + Vite single-page application, installable as a
PWA, served as static assets reachable on the local network. It performs no
facial recognition, no camera access, and no client-side caching of
attendance or biometric data — every business decision (RBAC, verification,
duplicate blocking) stays server-side in Feature 001, exactly per the
constitution's contract-first UI principle.

## Technical Context

**Language/Version**: TypeScript 5.x on Node.js 20 LTS (build tooling only;
shipped output is static HTML/CSS/JS)

**Primary Dependencies**: React 18, Vite, `vite-plugin-pwa` (manifest +
service worker for the app shell only), React Router, `openapi-typescript`
(dev-only, generates types from `local-api.yaml`)

**Storage**: N/A for attendance/business data — no client-side database, no
offline cache of employees, verification results, or biometric data (FR-017).
The auth token lives in memory/`sessionStorage` only, cleared on logout or
tab close.

**Testing**: Vitest + React Testing Library for component/unit tests; Mock
Service Worker (MSW) to fake `local-api.yaml` responses for integration
tests, mirroring Feature 001's fake-camera/fake-face-engine testing pattern
so the suite never needs a live backend or real hardware.

**Target Platform**: Modern mobile, tablet, and PC web browsers on the same
local Wi-Fi network as the Feature 001 backend; installable as a PWA where
the browser/OS supports it, but installability is not required for this
feature's user value (see Assumptions in spec.md).

**Project Type**: Web frontend, paired with the existing local backend from
Feature 001.

**Performance Goals**: UI overhead negligible beyond the local API's own
response time; initial screen interactive in under 2 seconds on the local
network; verification result rendered immediately upon API response, keeping
the guard's end-to-end flow within Feature 001's 5-second budget (spec
001 SC-001).

**Constraints**: Must work entirely against the local API with no internet
dependency; must never cache biometric or raw attendance data client-side;
must show a clear, non-technical connection-problem message when the local
API is unreachable (FR-008); role-based UI visibility must mirror backend
RBAC but must never be the only enforcement (FR-012); large touch-friendly
controls, no jargon, no configuration screens for guards (FR-015).

**Scale/Scope**: One guard post, one shared local network, a handful of
screens (login, attendance/verify, employee search, shift activity, and — for
administrators only — employee creation and face enrollment). Cloud
dashboard, reports, corrections, and NVR/video review are separate, later
features and are not touched here.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Local Attendance Truth and Offline Reliability**: PASS. The PWA holds
  no attendance truth itself; every read/write goes through Feature 001's
  local API, which already satisfies this principle. The PWA does require the
  local Wi-Fi link to the local PC to function, which is the same dependency
  the constitution already accepts for the guard workflow.
- **II. Verified Presence and Complete Auditability**: PASS. The guard must
  explicitly choose arrival or departure (FR-005); the UI never infers it.
  Success, failure, and duplicate-blocked outcomes are shown as distinct,
  clearly labeled results (FR-007, FR-010), mirrored directly from the
  attempt/event data Feature 001 already produces.
- **III. Backend-Enforced RBAC and Data Protection**: PASS. FR-011/FR-012
  state explicitly that hiding admin-only actions in the UI is a usability
  convenience, not the security boundary; Feature 001's backend RBAC is the
  actual enforcement. FR-017 prohibits any client-side caching of biometric
  data.
- **IV. Guard-First Simplicity and Contract-First UI**: PASS. FR-014/FR-015
  encode the three-taps/large-controls/no-jargon requirements directly. The
  UI is built entirely against Feature 001's already-frozen
  `local-api.yaml` contract, with mock fixtures (Phase 1) so frontend work
  does not depend on a running backend.
- **V. Incremental SDD and Testable Delivery**: PASS. This feature is
  independently testable via its own quickstart scenarios and does not
  require the cloud dashboard, reports, or corrections features to exist.

No constitution violations. Complexity Tracking is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-guard-pwa-interface/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── mock-responses.md   # Phase 1 output: example payloads per screen state
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── public/
│   └── icons/                      # PWA manifest icons
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes.tsx
│   ├── api/
│   │   ├── client.ts                # thin typed fetch wrapper (auth header, error mapping)
│   │   ├── types.ts                  # generated from specs/001-local-attendance-core/contracts/local-api.yaml
│   │   ├── auth.ts                   # POST /auth/login
│   │   ├── employees.ts              # GET/POST /employees, PATCH /employees/{id}, POST /employees/{id}/face
│   │   └── attendance.ts             # POST /attendance/verify, GET /attendance/shift-activity, GET /dashboard/overview
│   ├── auth/
│   │   └── SessionContext.tsx        # holds token + role, exposes login/logout, redirects on expiry
│   ├── components/
│   │   ├── Button.tsx                # large touch-friendly primitive
│   │   ├── ResultBanner.tsx           # success/failure/duplicate/connection-problem states
│   │   └── EmployeeListItem.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx              # FR-001, FR-002
│   │   ├── AttendancePage.tsx         # US1: select employee, choose type, verify, see result
│   │   ├── EmployeeSearchPage.tsx     # US2: search/select active employee
│   │   ├── ShiftActivityPage.tsx      # US3
│   │   ├── EmployeeManagementPage.tsx # US4, admin-only
│   │   └── FaceEnrollmentPage.tsx     # US4, admin-only
│   └── styles/
│       └── tokens.css                 # shared spacing/color/typography for large controls
└── tests/
    ├── unit/                          # component-level tests (Vitest + RTL)
    └── integration/                   # page-level flows against MSW-mocked local API
```

**Structure Decision**: Single `frontend/` project (React + Vite + TypeScript)
alongside the existing `backend/` from Feature 001, matching the repository's
already-planned web-application layout. The production build
(`frontend/dist/`) is served as static assets by the Feature 001 FastAPI app
(a `StaticFiles` mount) so the guard post runs one process instead of two —
this is an implementation detail for `/speckit-tasks`, not a contract change;
`local-api.yaml` is unaffected. During development, Vite's dev server runs
separately and calls the local API directly via its local network base URL.

## Phase 0: Research

Research output is captured in [research.md](./research.md): stack choices
(React/Vite/TypeScript, typed API client generation, session state, PWA app
shell only, testing strategy, static-file serving) and the deliberate
deferral of the local HTTPS/PWA-installability decision, consistent with how
Feature 001's own research.md already deferred it.

## Phase 1: Design and Contracts

Design outputs:

- [data-model.md](./data-model.md) — client-side view models (Guard Session,
  Employee Search Result, Attendance Verification Outcome, Shift Activity
  Item), all sourced from Feature 001's contract with no new persistence.
- [contracts/mock-responses.md](./contracts/mock-responses.md) — example
  payloads for every screen state, enabling mock-driven UI development
  before the backend is called for real.
- [quickstart.md](./quickstart.md) — manual validation scenarios covering all
  four user stories plus the unreachable-API edge case.

### Post-Design Constitution Check

- **Local-first recording**: PASS. No new data model or persistence was
  introduced; the design only adds client-side view models over Feature
  001's existing contract.
- **Auditability**: PASS. `data-model.md`'s Attendance Verification Outcome
  and Shift Activity Item both preserve the success/failed/duplicate_blocked
  distinction from the API without collapsing or reinterpreting it.
- **RBAC/data protection**: PASS. `data-model.md`'s Guard Session explicitly
  notes that `role` must never be treated as a security boundary in UI code;
  no biometric fields appear anywhere in the client-side models.
- **Guard simplicity**: PASS. `contracts/mock-responses.md` gives a
  contributor everything needed to build the plain-language result screens
  without guessing at wording or waiting on a live backend.
- **Testable delivery**: PASS. `quickstart.md` provides five independently
  runnable validation scenarios, matching the four user stories plus the
  connection-error edge case.

## Complexity Tracking

Not applicable — no constitution violations were identified.

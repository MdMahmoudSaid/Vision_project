# Tasks: Guard PWA Local Interface

**Input**: Design documents from `/specs/002-guard-pwa-interface/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mock-responses.md, quickstart.md

**Tests**: Included, matching how Feature 001 was implemented and per this plan's chosen testing stack (Vitest + React Testing Library + MSW) — automated tests never require a live backend or real hardware, only the mock fixtures in contracts/mock-responses.md.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently, mirroring Feature 001's approach.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the frontend project and its build/test tooling.

- [x] T001 Create frontend project directory structure (src/api, src/auth, src/components, src/pages, src/styles, tests/unit, tests/integration, tests/msw, public/icons) per plan.md in frontend/
- [x] T002 Create frontend/package.json with React 18, Vite, TypeScript, vite-plugin-pwa, React Router, openapi-typescript (dev), Vitest, React Testing Library, and MSW dependencies; create frontend/tsconfig.json and frontend/index.html
- [x] T003 [P] Create frontend/vite.config.ts with the React and vite-plugin-pwa plugins configured for app-shell caching only (no caching of local API responses, per research.md)
- [x] T004 [P] Create frontend/vitest.config.ts and frontend/tests/setup.ts for the Vitest + React Testing Library + jsdom environment
- [x] T005 [P] Create frontend/tests/msw/server.ts with the base Mock Service Worker setup (empty handlers array, wired for both dev and test use)
- [x] T006 [P] Create frontend/src/routes.tsx as a route table skeleton (login, attendance, employee search, shift activity, employee management, face enrollment paths; no page components wired yet)
- [x] T007 [P] Create frontend/src/main.tsx rendering a placeholder App per frontend/index.html
- [x] T008 [P] Generate TypeScript types from specs/001-local-attendance-core/contracts/local-api.yaml into frontend/src/api/types.ts using openapi-typescript, with a "generate:api-types" script added to frontend/package.json

**Checkpoint**: Frontend project builds, tests run (empty), and types are available from the frozen Feature 001 contract.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Session/auth handling, the typed API client base, and shared UI primitives every user story depends on.

**CRITICAL**: No user story work should begin until this phase is complete.

- [x] T009 Implement a typed fetch client base (auth header injection, JSON parsing, and error normalization for 400/401/403/network-failure into one consistent shape) in frontend/src/api/client.ts
- [x] T010 [P] Implement the POST /auth/login API function in frontend/src/api/auth.ts
- [x] T011 [P] Implement SessionContext (token + role held in memory/sessionStorage only, login/logout, auto-logout when any call returns 401) in frontend/src/auth/SessionContext.tsx
- [x] T012 [P] Implement the shared large, touch-friendly Button component in frontend/src/components/Button.tsx
- [x] T013 [P] Implement the shared ResultBanner component covering success/failure/duplicate-blocked/connection-error visual states in frontend/src/components/ResultBanner.tsx
- [x] T014 Implement LoginPage (form, calls auth.ts, redirects on success, shows an invalid-credentials message) in frontend/src/pages/LoginPage.tsx
- [x] T015 Wire frontend/src/App.tsx so unauthenticated users are redirected to LoginPage and authenticated users see a role-based navigation shell
- [x] T016 [P] Create MSW handlers for POST /auth/login (success and 401), sourced from contracts/mock-responses.md, in frontend/tests/msw/handlers/auth.ts
- [x] T017 [P] Unit tests for SessionContext (login success, login failure, logout, auto-logout on 401) in frontend/tests/unit/SessionContext.test.tsx
- [x] T018 [P] Integration test for LoginPage (successful redirect, invalid-credentials message) in frontend/tests/integration/LoginPage.test.tsx

**Checkpoint**: A user can log in and out, session state is managed, and shared UI primitives exist — user story implementation can now begin.

---

## Phase 3: User Story 1 - Record Attendance in Three Taps (Priority: P1) 🎯 MVP

**Goal**: A logged-in guard selects an active employee, chooses arrival or departure, triggers verification, and sees a clear success, failure, or duplicate-blocked result.

**Independent Test**: Log in as a guard, select the one pre-enrolled active employee, choose arrival, trigger verification, and confirm the result matches the outcome from the local API in at most three actions after login.

### Tests for User Story 1

- [x] T019 [P] [US1] MSW handlers for GET /employees (basic list), sourced from contracts/mock-responses.md, in frontend/tests/msw/handlers/employees.ts
- [x] T020 [P] [US1] MSW handlers for POST /attendance/verify covering success, failed, duplicate_blocked, and 400 error cases, sourced from contracts/mock-responses.md, in frontend/tests/msw/handlers/attendance.ts
- [x] T021 [P] [US1] Integration test: successful arrival shows a success result linked to employee, type, and time in frontend/tests/integration/AttendancePage.success.test.tsx
- [x] T022 [P] [US1] Integration test: failed verification shows a failure result and never implies attendance was recorded in frontend/tests/integration/AttendancePage.failure.test.tsx
- [x] T023 [P] [US1] Integration test: duplicate-blocked result is visually and textually distinct from a failure in frontend/tests/integration/AttendancePage.duplicate.test.tsx
- [x] T024 [P] [US1] Integration test: an unreachable local API shows a connection-error state instead of hanging or a misleading result in frontend/tests/integration/AttendancePage.connectionError.test.tsx

### Implementation for User Story 1

- [x] T025 [P] [US1] Implement the GET /employees API function (basic list, no query parameter yet) in frontend/src/api/employees.ts
- [x] T026 [P] [US1] Implement the POST /attendance/verify API function in frontend/src/api/attendance.ts
- [x] T027 [US1] Implement AttendancePage: employee list selection, arrival/departure toggle, verify action, and result rendering via ResultBanner in frontend/src/pages/AttendancePage.tsx
- [x] T028 [US1] Surface network/connection failures from api/client.ts through AttendancePage as the connection-error ResultBanner state in frontend/src/pages/AttendancePage.tsx
- [x] T029 [US1] Wire AttendancePage into frontend/src/routes.tsx and frontend/src/App.tsx as the default post-login page

**Checkpoint**: User Story 1 works independently and proves the MVP: a guard can record verified attendance in at most three taps after login.

---

## Phase 4: User Story 2 - Find the Right Employee Quickly (Priority: P2)

**Goal**: A guard searches for an employee by partial name or employee number and sees only matching active employees.

**Independent Test**: Search a set of employees by partial name and by employee number, and confirm only active employees matching the search appear, ready for selection.

### Tests for User Story 2

- [x] T030 [P] [US2] MSW handler variants for GET /employees?query= covering matches, no matches, and inactive-excluded cases in frontend/tests/msw/handlers/employees.ts
- [x] T031 [P] [US2] Integration test: search filters to matching active employees only in frontend/tests/integration/EmployeeSearchPage.test.tsx (consolidated with T032/T033 in one file, not three)
- [x] T032 [P] [US2] Integration test: an inactive employee never appears as selectable even when its name matches the search in frontend/tests/integration/EmployeeSearchPage.test.tsx (consolidated, see T031)
- [x] T033 [P] [US2] Integration test: a search with no matches shows a clear message instead of an empty or confusing screen in frontend/tests/integration/EmployeeSearchPage.test.tsx (consolidated, see T031)

### Implementation for User Story 2

- [x] T034 [US2] Extend the GET /employees API function to accept a query parameter in frontend/src/api/employees.ts (also sends active=true server-side; see note below)
- [x] T035 [US2] Implement EmployeeSearchPage with a search input, filtered results list, and a no-matches state in frontend/src/pages/EmployeeSearchPage.tsx (also fetches a default list on mount per FR-014, beyond the original task wording)
- [x] T036 [US2] Wire employee selection in AttendancePage to use EmployeeSearchPage's search-and-select flow in frontend/src/pages/AttendancePage.tsx
- [x] T037 [US2] Wire EmployeeSearchPage into frontend/src/routes.tsx

**Checkpoint**: User Stories 1 and 2 both work independently — a guard can now find and verify any active employee, not just the first one in a short list.

---

## Phase 5: User Story 3 - Review Recent Shift Activity (Priority: P3)

**Goal**: A logged-in guard or administrator reviews recent local attendance activity with outcomes clearly labeled.

**Independent Test**: Generate one successful verification, one failed verification, and one duplicate-blocked attempt, then open shift activity and confirm each outcome is labeled distinctly.

### Tests for User Story 3

- [x] T038 [P] [US3] MSW handler for GET /attendance/shift-activity with mixed outcomes (success, failed, duplicate_blocked) in frontend/tests/msw/handlers/shiftActivity.ts
- [x] T039 [P] [US3] Integration test: shift activity lists recent events with employee, type, time, and a plainly worded outcome in frontend/tests/integration/ShiftActivityPage.test.tsx
- [x] T040 [P] [US3] Integration test: failed and duplicate-blocked entries are visually distinguished from successful attendance events in frontend/tests/integration/ShiftActivityPage.distinct.test.tsx

### Implementation for User Story 3

- [x] T041 [US3] Implement the GET /attendance/shift-activity API function in frontend/src/api/attendance.ts
- [x] T042 [US3] Implement ShiftActivityPage (list rendering, outcome labeling and distinct styling) in frontend/src/pages/ShiftActivityPage.tsx
- [x] T043 [US3] Wire ShiftActivityPage into frontend/src/routes.tsx and the navigation shell in frontend/src/App.tsx

**Checkpoint**: User Stories 1-3 all work independently — guards can verify attendance, find employees, and review recent activity.

---

## Phase 6: User Story 4 - Manage Employees and Enroll Faces When Authorized (Priority: P4)

**Goal**: An administrator creates employees and starts face enrollment through the same interface; a guard without authorization never sees these actions.

**Independent Test**: Log in as an administrator, create an employee, start face enrollment, and confirm the same actions are absent from the interface when logged in as a guard.

### Tests for User Story 4

- [x] T044 [P] [US4] MSW handlers for POST /employees and POST /employees/{employee_id}/face covering success, 403 forbidden, and 400 capture_unusable cases, sourced from contracts/mock-responses.md, in frontend/tests/msw/handlers/employeeManagement.ts
- [x] T045 [P] [US4] Integration test: an administrator sees and can complete employee creation and face enrollment in frontend/tests/integration/EmployeeManagementPage.admin.test.tsx
- [x] T046 [P] [US4] Integration test: the guard role never sees employee creation or face enrollment actions in frontend/tests/integration/EmployeeManagementPage.guardHidden.test.tsx
- [x] T047 [P] [US4] Integration test: direct navigation to an admin-only route as a guard still results in the underlying API call being rejected, proving the UI hiding is not the only protection in frontend/tests/integration/EmployeeManagementPage.directAccess.test.tsx

### Implementation for User Story 4

- [x] T048 [US4] Implement the POST /employees and POST /employees/{employee_id}/face API functions in frontend/src/api/employees.ts
- [x] T049 [US4] Implement EmployeeManagementPage (employee creation form) in frontend/src/pages/EmployeeManagementPage.tsx
- [x] T050 [US4] Implement FaceEnrollmentPage (trigger enrollment, show usable/rejected result via ResultBanner) in frontend/src/pages/FaceEnrollmentPage.tsx
- [x] T051 [US4] Implement role-based navigation visibility that hides admin-only items for the guard role in frontend/src/App.tsx
- [x] T052 [US4] Wire EmployeeManagementPage and FaceEnrollmentPage into frontend/src/routes.tsx with a role guard that redirects, while relying on the backend's own 403 for actual enforcement

**Checkpoint**: All four user stories work independently, matching every acceptance scenario in spec.md.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Visual consistency, documentation, deployment wiring, and final validation.

- [x] T053 [P] Add PWA manifest icons in frontend/public/icons/ and finalize vite-plugin-pwa manifest metadata in frontend/vite.config.ts
- [x] T054 [P] Apply shared style tokens (spacing/color/typography sized for large touch controls) consistently across all pages in frontend/src/styles/tokens.css
- [x] T055 Audit frontend/src/ to confirm no client-side storage of biometric or raw attendance data beyond the in-memory/sessionStorage auth token (FR-017)
- [x] T056 [P] Create frontend/README.md with setup, dev server, and test commands, and the static-file-serving note from plan.md's Structure Decision
- [x] T057 Mount frontend/dist/ as static files in the Feature 001 backend per plan.md's Structure Decision in backend/src/local_attendance/main.py
- [ ] T058 Run quickstart.md scenarios manually against the real Feature 001 backend and record results in frontend/README.md (previously marked done with no supporting evidence in frontend/README.md; the app did not build at all until a subsequent code-review pass fixed a dozen bugs — this still needs genuine manual validation on real hardware)
- [x] T059 Run the full frontend test suite (unit + integration) and fix any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP first.
- **User Story 2 (Phase 4)**: Depends on Foundational and on User Story 1's AttendancePage/employees.ts existing to extend, but is independently testable on its own search behavior.
- **User Story 3 (Phase 5)**: Depends on Foundational; independent of US1/US2 beyond shared components.
- **User Story 4 (Phase 6)**: Depends on Foundational; independent of US1-US3 beyond shared components and the navigation shell.
- **Polish (Phase 7)**: Depends on all implemented user stories.

### User Story Dependencies

- **US1 Record Attendance**: Requires foundational session/auth, API client, and shared components.
- **US2 Find the Right Employee**: Requires foundational layer and extends US1's employees.ts/AttendancePage rather than duplicating them.
- **US3 Review Shift Activity**: Requires foundational layer only.
- **US4 Manage Employees and Enroll Faces**: Requires foundational layer and the role-aware navigation shell from Phase 2.

### Within Each User Story

- Tests are listed before implementation and should be written first when practical.
- API functions precede the pages that call them.
- Pages precede wiring them into routes/navigation.
- Each checkpoint should pass before moving to the next dependent phase.

## Parallel Opportunities

- Setup tasks T003-T008 can all run in parallel once T001-T002 complete (each touches a different file).
- Foundational tasks T010-T013 can run in parallel; T016-T018 (MSW handlers and tests) can run in parallel with each other.
- Contract/integration test tasks inside each user story can run in parallel because they target separate test files.
- US3 and US4 can proceed in parallel with each other and with US2 once Phase 2 is complete, since they touch different pages and API modules.

## Parallel Example: User Story 1

```bash
Task: "T019 [US1] MSW handlers for GET /employees in frontend/tests/msw/handlers/employees.ts"
Task: "T020 [US1] MSW handlers for POST /attendance/verify in frontend/tests/msw/handlers/attendance.ts"
Task: "T021 [US1] Integration test: successful arrival in frontend/tests/integration/AttendancePage.success.test.tsx"
Task: "T022 [US1] Integration test: failed verification in frontend/tests/integration/AttendancePage.failure.test.tsx"
Task: "T023 [US1] Integration test: duplicate-blocked result in frontend/tests/integration/AttendancePage.duplicate.test.tsx"
Task: "T024 [US1] Integration test: connection error in frontend/tests/integration/AttendancePage.connectionError.test.tsx"
```

## Parallel Example: User Story 4

```bash
Task: "T044 [US4] MSW handlers for POST /employees and POST /employees/{employee_id}/face in frontend/tests/msw/handlers/employeeManagement.ts"
Task: "T045 [US4] Integration test: admin can manage employees and enroll faces in frontend/tests/integration/EmployeeManagementPage.admin.test.tsx"
Task: "T046 [US4] Integration test: guard never sees admin actions in frontend/tests/integration/EmployeeManagementPage.guardHidden.test.tsx"
Task: "T047 [US4] Integration test: direct navigation still enforced server-side in frontend/tests/integration/EmployeeManagementPage.directAccess.test.tsx"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 Setup.
2. Complete Phase 2 Foundational.
3. Complete Phase 3 US1.
4. Stop and validate: a guard can log in and record verified attendance with a clear result in at most three taps.

### Incremental Delivery

1. Add US2 so guards can find any employee, not just the first one in a short list.
2. Add US3 so guards and admins can review recent shift activity.
3. Add US4 so administrators can manage employees and enroll faces from the same interface, with guards never seeing those actions.
4. Finish Phase 7 polish, static-file wiring into the Feature 001 backend, and quickstart validation.

## Notes

- Keep every business decision (RBAC, verification outcome, duplicate blocking) server-side in Feature 001; this frontend only displays and triggers, never decides.
- Do not cache biometric data or attendance/employee data client-side; the auth token is the only thing held across requests, and only in memory/sessionStorage.
- Do not implement facial recognition, camera access, offline phone storage, cloud dashboard, reports, manual corrections, or NVR/video features in this feature.
- Use MSW-mocked responses from contracts/mock-responses.md in all automated tests; real backend/hardware validation belongs to quickstart.md.

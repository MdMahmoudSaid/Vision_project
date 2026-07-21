# Quickstart: Guard PWA Local Interface

This guide validates the feature end to end once implementation tasks are
complete. It is intentionally a validation guide, not implementation code.

## Prerequisites

- Feature 001's local backend is running and reachable on the local network
  (see `backend/README.md`), with at least one seeded admin and one guard
  account (`scripts/create_local_user.py`).
- At least one active employee exists with a usable facial reference (for
  Scenario 1) and at least one active employee without one (for the missing
  face reference edge case).
- The guard PWA's dev server or production build points at the backend's
  local network address.

## Setup

```bash
cd frontend
npm install
npm run dev -- --host   # exposes the dev server on the local network for phone/tablet testing
```

Expected outcome: the app loads in a browser and shows the login screen; no
console errors about unreachable API calls until a request is actually made.

## Scenario 1: Guard records attendance in three taps (US1)

1. Log in as the guard account.
2. Select the pre-enrolled active employee (via search from Scenario 2, or
   directly if only one exists).
3. Choose "Arrival."
4. Trigger verification.

Expected outcomes:

- A clear success result appears, matching
  `contracts/mock-responses.md`'s `POST /attendance/verify` success example.
- No more than three actions were needed after login: select employee, choose
  type, trigger verification.
- Repeating immediately with the same employee/type shows a duplicate-blocked
  result, distinct from both success and failure.

## Scenario 2: Guard finds the right employee (US2)

1. Log in as the guard account.
2. Type a partial name, then a partial employee number, into the search field.

Expected outcomes:

- Only active employees matching the search text appear.
- An inactive employee does not appear as selectable, even if their name
  matches the search text.
- Searching for text that matches nothing shows a clear "no matches" message,
  not an empty or broken-looking screen.

## Scenario 3: Guard reviews recent shift activity (US3)

1. Generate one successful verification, one failed verification, and one
   duplicate-blocked attempt (via Scenario 1 and repeated attempts).
2. Open the shift activity view.

Expected outcomes:

- All three appear, each labeled with its outcome.
- The failed and duplicate-blocked entries are visually distinguished from
  the successful attendance event — neither is presented as recorded
  attendance.

## Scenario 4: Administrator manages employees and enrolls faces (US4)

1. Log in as the admin account.
2. Confirm employee creation and face enrollment actions are visible.
3. Create a new employee, then start face enrollment for them.
4. Log out, log in as the guard account, and confirm those same actions are
   not shown anywhere in the guard's navigation.

Expected outcomes:

- The admin can complete both actions using the same plain wording as the
  rest of the interface.
- The guard account never sees employee creation or face enrollment controls.
- If the guard's browser is pointed directly at an admin-only route/URL, the
  backend still rejects the underlying API call (403) — confirming the UI
  hiding is not the only protection (FR-012).

## Scenario 5: Local API unreachable

1. Stop the Feature 001 backend (or disconnect from the local Wi-Fi network).
2. Attempt to search for an employee or trigger verification.

Expected outcomes:

- A clear, non-technical connection-problem message appears within a few
  seconds, matching the "client-only state: connection error" example in
  `contracts/mock-responses.md`.
- The interface does not appear to hang indefinitely or show a misleading
  success/failure result.

## Test Commands

```bash
cd frontend
npm test              # Vitest unit + component tests
npm run test:integration   # MSW-backed page-level flow tests
```

Expected outcome: tests cover login, employee search filtering, all three
verification outcomes, shift activity labeling, role-based visibility of
admin-only actions, and the connection-error state — all against mocked
`local-api.yaml` responses, no live backend or camera required.

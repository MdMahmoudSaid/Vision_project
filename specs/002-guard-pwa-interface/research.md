# Research: Guard PWA Local Interface

## Decision: React + Vite + TypeScript for the guard PWA

**Rationale**: The project plan and constitution already confirm React/Vite
for the guard PWA. TypeScript lets the UI derive types directly from
Feature 001's `local-api.yaml`, keeping the "contract-first UI" principle
enforceable at compile time rather than only by convention.

**Alternatives considered**: Plain JavaScript would drop the compile-time
contract checking. A different framework (Vue, Svelte) would work technically
but contradicts the stack already agreed with the client and documented in
`docs/plan_pointage_facial.md`.

## Decision: Generate API types with `openapi-typescript`, hand-write a thin fetch client

**Rationale**: The guard PWA calls a small, stable set of endpoints (login,
employee search/create, face enrollment, verify, shift activity, overview).
A full generated SDK (e.g. `openapi-typescript-codegen`) adds a large
generated-file surface for little benefit at this scale. Generating only the
request/response *types* from `local-api.yaml` and hand-writing a small fetch
wrapper keeps the dependency footprint minimal while still deriving accurate
types directly from the frozen contract, so a breaking API change fails the
TypeScript build instead of failing silently at runtime.

**Alternatives considered**: A full generated client SDK was rejected as
unnecessary generated-code overhead for ~7 endpoints. Untyped `fetch` calls
were rejected because they would silently drift from the contract.

## Decision: React Context for session state, component state elsewhere

**Rationale**: The app has one piece of cross-cutting state (the logged-in
user's token and role) and a handful of independent screens. A dedicated
state-management library (Redux, Zustand) would add complexity the "extremely
simple" UI mandate does not need.

**Alternatives considered**: Redux/Zustand were rejected as disproportionate
to the app's size. Prop-drilling the session through every page was rejected
as more error-prone than a single context.

## Decision: `vite-plugin-pwa` for the app shell only; no caching of API data

**Rationale**: The feature is named "PWA" and the constitution expects an
installable app shell, but FR-016/FR-017 explicitly forbid client-side
storage of attendance or biometric data. The service worker therefore caches
only static build assets (HTML/CSS/JS/icons) for faster reloads, and never
intercepts or caches `local-api.yaml` responses. Employee lists, verification
results, and shift activity are always fetched live.

**Alternatives considered**: Caching API responses for offline browsing was
rejected — it would let a guard see stale employee/attendance data without
realizing it, contradicting local-first correctness and this feature's
explicit "no offline phone storage" boundary (FR-016).

## Decision: Vitest + React Testing Library + MSW for automated tests

**Rationale**: Mirrors Feature 001's testing philosophy (fake camera/face
engine standing in for real hardware): Mock Service Worker fakes
`local-api.yaml` responses so component and page-level tests run without a
live backend, and are deterministic regardless of network/hardware state.
Vitest is the natural pairing for a Vite project (shared config/transform
pipeline with the dev server).

**Alternatives considered**: Running tests against a live local backend
instance was rejected as slow and hardware-dependent (the real backend can
depend on a real camera per Feature 001's own quickstart). A heavier E2E-only
strategy (Playwright against a full stack) was deferred to manual quickstart
validation rather than the automated suite, matching how Feature 001 treats
real-hardware validation as a manual, not automated, step.

## Decision: Serve the built PWA as static files from the Feature 001 backend

**Rationale**: The guard post is a single local PC. Running a second web
server just to host a handful of static files adds an extra process to keep
alive for no benefit; FastAPI's `StaticFiles` can serve `frontend/dist/`
directly. This is an implementation/deployment detail, not a contract change
— `local-api.yaml` and its base path are unaffected.

**Alternatives considered**: A separate static file server (nginx, Vite
preview server left running in production) was rejected as unnecessary
operational overhead for a single-PC deployment.

## Deferred: Local HTTPS / PWA installability strategy

**Status**: Explicitly out of scope for this feature's implementation, same
as Feature 001's research.md already concluded. The project constitution and
`docs/plan_pointage_facial.md` both flag the local HTTPS/certificate approach
(needed for full PWA installability on a guard's phone) as a Phase
0/deployment-and-stabilization decision, not core feature logic. This
feature's spec.md Assumptions section states installability is not required
for this feature's user value — the app must simply be usable over plain HTTP
on the local network during development and testing; the certificate
strategy is resolved when the project reaches deployment/stabilization.

**Rationale for deferring again here**: Blocking this feature's UI
implementation on a certificate decision would stall guard-flow development
for a concern that is identical across every local-network feature, not
specific to this one.

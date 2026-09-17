# Build Plan

## Phase 0 — Foundation

- scaffold responsive web app
- strict TypeScript
- formatting/linting
- test setup
- environment validation
- database migrations
- auth shell
- storage shell
- provider interfaces
- analytics abstraction

Exit criteria:

- app runs locally
- tests run
- CI command documented
- database can migrate
- signed-in user shell exists

## Phase 1 — Thin vertical slice with fixtures

- sourcing form
- request persistence
- deterministic constraint normalization for basic fields
- fixture candidate dataset
- hard filter
- scoring
- result card
- save/reject
- basic history

Exit criteria:

- complete happy path works without live search
- Test Case 1 can be executed with fixtures
- ranking is inspectable

## Phase 2 — Live retrieval

- search adapter
- candidate normalization
- URL canonicalization
- dedupe
- evidence model
- verification adapter
- caching

Exit criteria:

- live candidates can become normalized verified products
- unsupported/unknown facts remain unknown

## Phase 3 — AI interpretation

- structured natural-language constraint extraction
- image analysis
- query generation
- compatibility reasoning
- grounded explanation generation

Exit criteria:

- outputs pass schemas
- retries/fallbacks work
- no live product fact comes only from the model

## Phase 4 — Replacement loop

- structured rejection reasons
- feedback persistence
- near-duplicate suppression
- one-item replacement

## Phase 5 — V0 evaluation

- usefulness-vs-normal survey
- serious-contender count
- internal constraint-violation review
- request latency/cost report

## Explicitly later

- voice
- live camera
- AR
- native apps
- checkout
- procurement

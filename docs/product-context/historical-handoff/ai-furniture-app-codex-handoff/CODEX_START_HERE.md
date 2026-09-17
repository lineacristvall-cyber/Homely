# Codex — Start Here

This repository is for the **V0 of an AI furniture sourcing agent for interior designers**.

## Goal

Prove one hypothesis:

> Can the app provide five more useful, purchase-ready recommendations than a designer's normal Google/Pinterest sourcing process because it understands all project constraints at once?

## Start sequence

Read:

1. `AGENTS.md`
2. `docs/PRODUCT_SPEC.md`
3. `docs/AI_PIPELINE.md`
4. `docs/DATA_MODEL.md`
5. `docs/TEST_CASES.md`
6. `docs/BUILD_PLAN.md`

Then implement **Phase 0 + Phase 1** from `docs/BUILD_PLAN.md`.

## Product boundary

The app is not a general interior-design platform. It is a sourcing agent.

The central workflow is:

```text
request → understand → search → verify → filter → rank → explain → 5 options → feedback/replacement
```

## Default technical direction

Unless the existing repo already has a coherent stack:

- responsive web app
- Next.js + TypeScript
- PostgreSQL
- Supabase is acceptable for V0 auth/database/storage
- schema validation for all AI/external data
- external providers behind interfaces

Avoid hard-coding the application to one search provider or one AI provider.

## Critical trust rule

Never fabricate live commerce facts. Unknown is better than false certainty.

## First deliverable

Create a thin end-to-end slice with mocked candidates if necessary:

- create sourcing request
- normalize constraints
- score/filter candidate fixtures
- render five result cards
- save/reject feedback
- persist the request

Then connect live retrieval in the next phase.

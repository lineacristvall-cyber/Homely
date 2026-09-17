# Codex Bootstrap Prompt

Read `AGENTS.md`, `CODEX_START_HERE.md`, and all documents linked from them.

Then build **Phase 0 and Phase 1 only** from `docs/BUILD_PLAN.md`.

Key constraints:

- responsive desktop-first web app
- strict TypeScript
- product domain types separated cleanly
- provider interfaces for AI/search/verification/storage/analytics
- database migrations
- reference-image upload shell
- sourcing request form containing the nine canonical inputs
- fixture-based candidate set for the first thin vertical slice
- hard-constraint filtering before ranking
- deterministic, inspectable initial scoring
- five results if five valid fixture products exist
- save / reject + reason
- basic request history
- unit tests for budget normalization, exclusions, dimensions, and ranking
- loading and error states
- no live voice/camera/AR/native app/checkout/procurement

Do not hide assumptions. Record meaningful architecture choices in `docs/DECISIONS.md`.

Before finishing:

- run lint
- run typecheck
- run tests
- summarize files changed
- summarize any open questions that block Phase 2

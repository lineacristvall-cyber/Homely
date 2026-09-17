# Homely developer handoff

This public source snapshot includes the latest application and the context used to build it. It is a local POC, not a hosted production service. Public repository access is not access to the existing Supabase account or its private data.

## Read in this order

1. README.md: portable startup and configuration.
2. docs/product-context/CURRENT_CONTEXT.md: current product direction, superseding historical material.
3. docs/product-context/mockups/14-approved-nine-step-flow.png: approved visual target.
4. docs/product-context/flows/ and architecture/: editable user flows and architecture.
5. CONTRACTS.md: API and data boundaries.
6. PROGRESS.md, DECISIONS.md, OPEN_ACTION_ITEMS.md: evidence, decisions and remaining tasks.
7. artifacts/nine-step-flow-2026-09-17/TESTING_REPORT.md: actual test results and limitations. Serve its directory using `python -m http.server 8773 --directory artifacts/nine-step-flow-2026-09-17` to view the comparison.
8. backend/cloud/README.md and migrations/: cloud schema and ownership constraints.

## Verification and limits

The implementation report records 210 backend and 52 cloud tests passing. The publication check reran the full UI suite successfully: 36/36 passed. Real recovery email, device camera/voice and real merchant monitoring remain unverified. Photo selection is manual annotation, not automatic object segmentation. Numeric fit checks support bounded arrangements; absent evidence blocks fit-qualified recommendations. No exact stock/quantity merchant adapter, hosted scheduler, or email/push alert delivery is provided.

## Public snapshot exclusions

Environment files, credentials, runtime projects, private uploads, sessions and watch data are excluded. Earlier screenshot PNGs are excluded pending privacy review; their text reports remain. Final nine-step screenshots use documented stock/synthetic fixtures. Licensed image sources and attribution are in the fixture manifest. Historical handoff documents remain for context and do not override current decisions. No open-source license grant is implied by public visibility.

The cloud project origin is currently allowlisted in code. Use local mode initially; coordinate with the owner for authorized cloud configuration or a reviewed migration to a separate project. Never paste credentials into client-side code or commits.

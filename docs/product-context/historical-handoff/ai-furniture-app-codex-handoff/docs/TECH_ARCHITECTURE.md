# Technical Architecture

## V0 platform

Responsive web app, desktop-first.

## Suggested stack

- Next.js
- React
- TypeScript
- Tailwind CSS or equivalent
- PostgreSQL
- Supabase is acceptable for auth/database/storage
- test runner suitable for TypeScript
- browser/e2e tests for core user flow

Use stable supported releases when scaffolding.

## Service boundaries

```text
UI
 ↓
Application / API
 ├─ Auth
 ├─ Request service
 ├─ AI constraint service
 ├─ Image analysis service
 ├─ Search provider
 ├─ Product normalizer
 ├─ Product verifier
 ├─ Ranking service
 ├─ Recommendation service
 ├─ Feedback service
 └─ Analytics
 ↓
PostgreSQL / Object Storage
```

## Provider interfaces

Create adapters for:

- AI
- web/product search
- verification/fetching
- object storage
- analytics

The business logic should not import vendor SDKs everywhere.

## Security

- server-side secrets
- upload validation
- row-level access
- rate limits
- URL validation
- sanitize external content
- prompt-injection resistance
- no execution of external page content

## Observability

For each sourcing run, log:

- request id
- stage durations
- number of candidates
- filter counts
- provider errors
- AI parse retries
- cost counters
- final result ids

Do not log sensitive contents unnecessarily.

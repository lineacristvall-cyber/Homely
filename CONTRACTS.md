# Homely POC shared contract

Updated: 2026-09-13. Owner: integration supervisor. Workers must read `PROGRESS.md`, `DECISIONS.md`, `OPEN_ACTION_ITEMS.md` before editing and report progress to supervisor. This is a same-origin JSON API served by `backend/server.py`; front-end assets live in `web/`. All prices are USD. Unknown is `null`, never 0.

## Project
`{id,name,mode,version,createdAt,brief,room,candidates,decisions}`. `brief` is `{itemType,quantity,style,location,flexibleTarget,hardCap,notes,measurements}` with optional setup fields `roomType` (`dining|living|bedroom|other`), `roomLabel` (text, max100), `furnishingMode` (`keep|from_scratch|null`) and `retainedItems` (max20 explicit names, max100 each). Partial brief patches preserve unrelated fields. Cloud project JSON and owner exports retain these fields; disclosure preview remains explicitly scoped to its existing allowlist. Measurements are `{tableUndersideIn,chairArmIn,roomWidthIn,roomDepthIn}` (nullable). `room` is `{imageUrl,uploadedAt,consent}` or null.

## Candidate
`{id,title,seller,url,sourceId,exactSku,variant,imageUrl,unitPrice,shipping,tax,availableQuantity,observedAt,method,status,reason,dimensions,sourceRefs}`. `status` is `lead|ready|stale|unavailable`; no source query by itself grants ready. `reason` explains uncertainty. `dimensions` may include `widthIn,depthIn,heightIn,armHeightIn`. `sourceRefs` are attributable URL/record/time/method evidence. Ready eligibility is recomputed by server, not UI. `imageUrl` can be null.

## JSON endpoints
- `GET /api/health` -> `{ok,openaiConfigured}`.
- `GET /api/projects` -> `{projects:[...]}`.
- `POST /api/projects` body `{name,mode}` -> `{project}`.
- `GET /api/projects/{id}` -> `{project}`.
- `PATCH /api/projects/{id}/brief` body `{expectedVersion,brief}` -> `{project}` or 409.
- `POST /api/projects/{id}/room` body `{dataUrl,consent}` -> `{project}` or 400. A room image is never put in model calls without consent.
- `POST /api/projects/{id}/research` -> `{job}`; `GET /api/jobs/{id}` -> `{job}` with `queued|running|completed|failed|cancelled`, `progress`, `error`. On completion project candidates update.
- `POST /api/projects/{id}/product-urls` body `{url}` -> `{candidate,project}` or safe 422 for blocked sources. Public HTML/JSON-LD import always enters the lead lane.
- `POST /api/projects/{id}/visualizations` body `{candidateId,productImageDataUrl,productImageRightsConfirmed}` -> `{job}`. `GET /api/jobs/{id}` also provides `result` with `{imageUrl,illustrative,identityStatus,fitStatus,fitReason,sourceImageUrl,roomImageUrl}` if completed.
- `POST /api/projects/{id}/decisions` body `{candidateId}` -> `{decision}` or 400; decision contains delivered total and cap status.
- `POST /api/projects/{id}/handoff` body `{candidateId}` -> `{status,url,reason}`; only `status=ready` may expose seller URL after fresh exact evidence and hard-cap recheck.

## Module interfaces
`backend.sourcing.search_products(brief:dict, api_key:str|None) -> list[dict]` returns normalized candidates, with leads by default. `backend.sourcing.verify_candidate(candidate:dict, brief:dict, now:datetime|None=None) -> dict` returns candidate with computed status/reason; never trusts input status. `backend.visualization.create_visualization(room_path:Path, product_path:Path, candidate:dict, brief:dict, api_key:str|None, output_path:Path) -> dict` returns result fields; raises `ValueError` for missing consent/rights/data, and only claims illustrative output. Keep provider calls inside modules. The supervisor may adjust signatures with direct coordination.

## Cloud authentication and current extensions
The running preview uses `HOMELY_STORAGE=cloud` against the existing free Supabase project. Cloud routes require an opaque `homely_auth` HttpOnly/SameSite=Strict cookie; provider access/refresh tokens stay in server memory. Restarting the server ends app sessions. Local mode is explicit and does not expose cloud job/cache files. Cloud projects and private assets use owner-scoped RLS; background job state remains owner-scoped local files pending a durable worker.

- `GET /api/auth/session` returns `{mode,authenticated,user}`. No project reads before the session is known.
- `POST /api/auth/sign-up` accepts `{email,password}` and returns signup state including `email_confirmation_required` or `sign_in_required`; user enters credentials only in the app.
- `POST /api/auth/sign-in` accepts `{email,password}`, sets the opaque cookie, returns public user data. `POST /api/auth/sign-out` revokes the local session and clears its cookie.
- `GET /api/cloud-assets/{id}` authenticates ownership and proxies private image bytes. No service key or storage signed URL is exposed to browser code.
- `POST /api/projects/{id}/assistant` accepts `{message,expectedVersion}`. Grounded allowlisted actions that change state return a one-use browser/project/version-scoped confirmation. Submit `{confirmationId,expectedVersion}` to execute. A stale version returns409. Visualization routing opens input/consent UI; it does not silently generate an image.
- `POST /api/transcriptions` accepts `{dataUrl,consent}` and returns `{text}` for editable review before the shared typed action route. Browser recording is bounded to60seconds/8MB; server limit10MiB. No spoken replies or realtime duplex voice are implemented.
- `POST /api/jobs/{id}/cancel` returns `{job}` with the actual terminal state. Queued/running jobs become cancelled; completed jobs remain completed. Cancellation prevents late project/result publication; it cannot guarantee a provider request already sent incurs no cost.
- Room and visualization submissions include `expectedVersion`. Publication rechecks the version after image upload under the mutation lock. A completed visualization becomes stale if the project changes. `sourceImageUrl` is the actual uploaded product reference; any merchant URL is separate.

## Actual attempted-source ledger (integration)
`search_products_with_coverage(brief,key)` returns `{candidates,coverage,coverageComplete:false}`; legacy `search_products` still returns a list. Coverage describes actual provider discovery and bounded page enrichment operations, including blocked/failed attempts, not all sites searched internally by the provider. `SourcingError.coverage` preserves partial failures. The integration stores `sourceCoverage` and `sourceCoverageComplete:false` on successful project/job results; failed jobs retain partial coverage without replacing project findings. Missing historical ledgers default to `[]`/`false`, never complete coverage.

## Export and visualization history
- `GET /api/privacy/export` returns the owner-scoped `homely.project-export.v1` JSON attachment with `Cache-Control: no-store`. Cloud export enumerates bounded owner-only keyset pages (up to1000 projects); overflow returns413 with no partial export. It is not a transactionally frozen account backup. Image files, jobs, audio, settings and unsaved drafts are excluded.
- `GET /api/projects/{id}/visualizations` returns `{jobs:[...]}`, at most50 recent owner/project-scoped visualization records. Corrupt or cross-owner records are omitted. Completed older-version results are served cancelled/stale using the same rule as individual job GET. New visualization jobs include `candidateId`; frontend restoration must match owner/project/candidate/version and never trigger a new provider call.
- `build_review_snapshot` is a pure selected-field disclosure preview with a content hash. It is not an access grant. No recipient sharing endpoint is implemented yet.

- `POST /api/projects/{id}/review-preview` accepts `{expectedVersion,scope}` and returns `{preview,canCreateReview:false}`. It authenticates owner, rechecks version, defaults all selections empty and makes no writes. Scope is `{candidateIds,noteFields,measurementFields,imageIds}`; only brief `notes` and the four existing measurement fields are accepted, and imageIds must currently be empty. Unknown selections fail400; stale version409. No link, recipient permission, approval, notification or share is created.

## Approved nine-step setup and fit contracts
- `brief.journey` is a closed bounded object: step (`room|intent|photo|measurements|keep|categories|preferences|fit|results|saved`), selectedCategories (max10 strings), retainedObjects (max20 `{id,label,variant,confirmed,anchor?}`), keepingDecision (`keep|fresh|later|null`), roomMeasurements (`width,depth,height,unit`), categoryOther, categoryGuideIndex and resultMode (`fit|inspiration`). Anchor normalized x/y must name this project's current room image; a replacement photo removes anchors. Decide-later is unknown, never start-fresh.
- `brief.fit` schemaVersion1: `retained_dining_table` validates confirmed table/variant, lowest apron/tabletop, opposing-row count/leg spacing/available depth and explicit tolerances; `room_layout` validates a confirmed unobstructed rectangle, height limit and exact full grid for a start-fresh project. Measurements carry value/unit/source/status and product-source URL. Unsupported layouts remain blocked.
- `GET /api/projects/{id}/fit` returns `{gate,candidates:[{candidateId,status,checks,reason,scope}]}`. A project-gate pass is not a product fit pass. Candidate evidence must bind exactSku/variant, and all applicable dimensions must pass.
- `POST /api/projects/{id}/fit-evidence` accepts `{expectedVersion,candidateId,fitEvidence}` and preserves other candidates. Evidence statuses unknown/conflicting block fit-qualified results.
- `POST /api/projects/{id}/retained-product` accepts `{expectedVersion,url}` and returns public parsed product details plus `requiresConfirmation:true`, with no writes and no automatic identity or measurement confirmation.
- Research accepts explicit mode `fit|inspiration`, defaults fit. Missing/conflicting project evidence blocks before any research-provider call. Inspiration is a distinct unqualified lane. Step/fit-only brief patches preserve research; relevant search brief changes invalidate it.
- Owner exports include bounded setup/fit evidence with existing redaction. Sharing-preview allowlist remains unchanged.


## Recovery, upload consent and opt-in price watches (September 17)
- Cloud capabilities now advertise passwordRecovery/confirmationResend. POST `/api/auth/recover` and `/api/auth/resend` accept email only and return generic eligibility messages. The latter is signup confirmation only. POST `/api/auth/reset` accepts `{tokenHash,newPassword}`; server verifies the hash as recovery with the configured provider, verifies the temporary user, updates only that authenticated user, invalidates local sessions for that owner and discards the recovery session. No provider token is returned or saved. Browser uses a pasted unopened recovery link/token; expired/consumed links require a new email. Normal origin/host/no-store protections apply. Real mail delivery and real account reset remain untested.
- Room upload accepts `uploadConsent:true` independently of optional image-provider `consent`. Upload permission does not authorize model processing. Legacy consent true remains accepted. New projects start with neutral furniture/quantity1; the journey explicitly selects categories.
- GET `/api/watches` returns the current owner's watches and in-app notifications, schedulerRunning and deliveryNote. POST `/api/projects/{id}/watches` requires current expectedVersion, candidateId and enabled true. Saving a decision never subscribes. Exact SKU/variant/price source evidence must be current (24h), matching and USD.
- POST `/api/watches/{id}/cancel` and `/api/notifications/{id}/read` require current owner. Local mode uses one explicit local-preview owner; cloud uses authenticated account ID. The private local JSON file is mode0600 and persists subscriptions/notifications. Default interval1hour. Checks run only while this server runs; no email/push, hosted scheduler or delivery guarantee. Failed/mismatched/stale observations do not generate price-change alerts.

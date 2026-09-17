# Frontend capability map

Updated 2026-09-13. Scope: local responsive POC, not production implementation of every screen/state.

## Real API-connected flow

- S01/S03: create professional or DIY local project; open existing project from desktop rail or mobile More project chooser. Cloud authentication is now wired when the server reports cloud mode; local mode stays separate.
- S02/S05: original room upload with required consent and local file validation; measured values editable in brief. Camera, multiple views, annotations, and permission preferences are upcoming.
- S04/S07/S15: room canvas and editable, versioned brief; separate target/hard cap; target validation; measurements; retained-furniture notes. Dirty drafts survive view changes and reload using per-project sessionStorage and explicitly say unsaved. Only successful save clears the draft. Findings use the saved brief rather than uncommitted draft budgets.
- S08/S09/S10/S12/S24: actual research start and job polling, error/empty recovery, ready/lead/stale/unavailable separation, product URL import as a lead, comparison and unknown delivered-cost evidence. Source coverage shows actual returned domain counts, ready counts, observation times, and explicit missing/partial coverage (no fabricated per-source checks).
- S11: candidate evidence modal, exact SKU/variant/count/method/time, cost breakdown, attributable source records. No frontend availability promotion.
- S13: explicit exact-product image and rights consent, visualization job request/poll/result, original/source lineage, illustrative disclosure and independent fit status. Generation requires backend/provider eligibility. No validated product-fidelity claim.
- S14/S16: comparison includes flexible target premium and absolute cap; saved decision uses actual server response.
- S17: server-gated seller handoff exposes external continuation only after ready response; blocks unsupported/unconfirmed outcomes visibly. No purchase claim.
- S23: offline notice, 409 draft preservation. Sync reconciliation is upcoming.

## Discoverable upcoming affordances

Every upcoming action opens a small **Not available yet** dialog and preserves the underlying view/form. No unsupported action runs and no success is fabricated.

- Spoken briefings/playback and recorded-audio history remain upcoming (S04/S07/S10). Typed and push-to-talk input, editable transcription, and proposal confirmation are now API-connected below.
- Camera capture, multiple room views, image quality, retained-piece annotation (S02/S05).
- Original/placement/measurement toolbar: original viewer and measurement navigation real; interactive placement/rotation/variant swaps upcoming (S13/S15).
- Inspiration boards, style tags, likes/dislikes, notes/files/vendors (S06).
- Source access settings, seller inquiries/manual confirmations, Marketplace/Craigslist access (S08/S11/S12).
- Pause/resume/cancel, saved hunts, cadence, quiet hours, notifications and stock-change alerts (S08/S18/S19).
- Client share/invite/revoke, scope preview, comments, approval/revision (S20).
- Mark purchased, receipts/orders/refunds/replacement ledger (S21).
- Team/billing, privacy/retention/delete/consent revocation, offline reconciliation (S22/S23).
- Project plan/archive, referrals/credits/returns (S03/S17/S21).

These are grouped navigable capability previews, not 24 fully built templates or 370 implemented branches.

## Design and validation

All 12 approved PNG references were inspected. UI aligns serif headings, dark teal/ivory/sage palette, desktop room-first canvas with brief inspector, canvas tabs, original/placement/measurement toolbar, and mobile bottom navigation. Empty rooms use an explicitly labeled CSS illustration; no mock source image or availability is passed off as real. The real preview was checked at 1440px desktop and 390px mobile with zero horizontal overflow. Mobile provides Edit brief directly under the room and hides decorative journey cards.

`web/tests/ui.test.cjs` uses Node's test runner and Playwright with mocked API records explicitly labeled as fixtures. Set `PLAYWRIGHT_MODULE` and `CHROME_PATH` for another machine. It verifies end-to-end flow behavior, budget validation, lead truth, unknown costs, comparison, decision/handoff blocking, mobile consent/dialog behavior, per-project draft persistence, mobile project chooser, and URL import.

QA follow-ups: evidence opens focused at the top; source records have safe clickable links and expandable technical details; comparison includes a swipe/scroll hint, keyboard-scrollable region, saved target plus difference-from-target, and product-specific checkbox names. Pause is inactive when no job is queued/running.


## Integrated typed and voice assistant (2026-09-13 follow-up)

- A persistent, expandable conversation bar is available on laptop/mobile. Header voice and room voice affordances open it. Project-scoped typed drafts survive navigation and reload; the bar clearly indicates when the saved brief differs from unsaved edits.
- Typed messages and edited voice transcripts share `POST /api/projects/{id}/assistant`, always with a captured project version. Mutation proposals show their exact server summary before explicit Confirm. Cancel issues no mutation. Confirmation uses the server's captured expectedVersion; a 409 leaves drafts intact and asks for a fresh proposal.
- Responses update projects/jobs only from real server objects. Commands can filter actual candidate IDs, open existing comparison, or open visualization consent/setup. Unknown candidate IDs are excluded/rejected. No frontend stock promotion, inferred success, or automatic voice action.
- Voice is off by default. Explicit consent precedes Start and browser microphone permission. MediaRecorder selects supported webm/mp4/ogg; recording has a 60-second / 8 MB bound. Stop uploads to `/api/transcriptions`; the transcript is editable before Send. Cancel, close, project switch, and page exit release tracks; stale/cancelled transcription results are ignored and abortable requests are aborted. Permission denial and unsupported recording leave typed fallback available.
- **Physical microphone and actual audio/transcription quality are not validated by the mocked suite.** UI displays that limit. No real microphone recording was initiated during these tests.
- Seven Playwright suites now cover prior flows plus typed proposal/cancel/confirm/version, command-driven compare/filter, explicit audio consent, permission-denied fallback, synthetic recording stop/review, track cleanup, and cancelled/stale transcription. Audio fixtures are synthetic test bytes, not a live provider validation.


## Auth and upload concurrency follow-up

- The app checks `/api/auth/session` before fetching projects. Cloud mode without a session shows sign-in/sign-up; it never fetches project data first. Sign-up shows the server confirmation/sign-in instructions. Sign-out hides private projects and cancels microphone/transcription state. Expired cloud sessions return to sign-in.
- Cloud account IDs namespace brief drafts, assistant drafts/conversation state, and last-open project. Returning to an account restores its own tab drafts; another account cannot see them through the UI. Local draft keys are migrated compatibly. This is UI isolation; actual RLS/private-storage enforcement remains the server's responsibility.
- Passwords are held only in the password input/request, cleared after submission, and never written to browser storage or conversation history.
- Room and visualization submissions capture project ID and expectedVersion before reading the image; 409 stops the action and asks for latest-project review, preserving the typed brief draft.
- Nine mocked browser suites pass including sign-in/signup/sign-out, no project reads before auth, two-account draft/history separation, and password non-persistence. **No live cloud auth was claimed or tested here. Signup consumes the actual server message and snake_case email_confirmation_required/sign_in_required contract.** Root still owns live cloud configuration/validation.
- One bounded real typed UI/API test passed on the local server: synthetic QA project stayed at quantity6 before confirmation, explicit confirmation updated it to4, and reload persisted4 with no browser exceptions. Actual microphone/transcription validation remains unverified.


## Cancellation, mode copy, and real source attempts

- Workspace and saved-brief labels reflect the actual auth mode: local preview or private cloud project. Signup footer explains email confirmation and sign-in in plain language.
- Cancel research calls `POST /api/jobs/{id}/cancel` with an empty JSON body and uses returned `{job}` status. Queued/running are cancellable; terminal jobs are not. Server-confirmed cancellation prevents an older poll response from restoring completion. If the server already completed the job, saved findings are shown with that explicit explanation. No cancellation is fabricated on request failure.
- Sources now uses `project.sourceCoverage` / `sourceCoverageComplete`, or the latest job's `result.sourceCoverage` / `sourceCoverageComplete` (including failed research). Actual records show sourceId, URL, stage, status, reason and observedAt. Completed/blocked/failed counts are operation counts. Finding-domain counts stay separate. Provider-internal attempted sites and internet breadth remain explicitly unavailable.
- Tests use mocked sources/audio/accounts only; no live provider call or signed-in user browser interaction was performed for this follow-up.

## Visualization reference/result usability follow-up

- The setup shows the original room beside the locally selected product image, plus known SKU/variant/source context. File selection alone does not upload anything. Changing the file clears both match and rights checks.
- Explicit product/variant match and image-use rights are both required before POST. The existing `productImageRightsConfirmed` assertion is sent only when both UI confirmations are checked; no new backend contract field was invented. Room consent and expectedVersion remain required.
- One pending generation per candidate is enforced in the UI, including after reopening the dialog. Actual queued/running/failed/cancelled state and job ID are visible; Cancel this preview uses the existing job cancel endpoint. Retry remains an explicit new request.
- Job/results are associated with account, project, candidate, and captured project version. A late result cannot appear in another candidate's open dialog. Cached previews from an earlier project version are withheld with a request-new-preview notice.
- Output remains clearly illustrative with unverified identity / unknown physical fit and specific missing-measurement reasons. Original-room and product-source links remain available. No imagery or fit was fabricated.
- All 13 mocked browser suites pass. New coverage checks file match/rights gates, pending duplicate prevention, candidate-specific late-result routing, source lineage links, and unknown-fit disclosure. No signed-in user browser or live provider was used.
- Real product upload has no identified UI blocker beyond required original room, supported JPEG/PNG/WebP file ≤15 MB, explicit product/variant match and usage rights. Source access/licensing and backend/provider eligibility remain separate constraints.


## Project JSON export

- Settings & privacy and mobile More now offer a working Download project JSON control. It fetches authenticated same-origin `GET /api/privacy/export` with no-store, downloads the returned JSON blob as `homely-project-export.json`, and reports loading, download-started, or retryable error. Late responses cannot download after account scope changes.
- The actual backend schema is `schemaVersion: homely.project-export.v1` with exportedAt, scope, projectCount, projects, redactionCount and limitations. The UI preserves that response without claiming a full backup.
- Copy explicitly excludes image binaries, account settings, jobs, audio and unsaved browser drafts. Source observations stay historical evidence, not renewed stock verification. No deletion control or deletion success was fabricated.
- All 15 mocked browser suites pass, including response-content/schema/filename download validation and a mobile failure path. The export tests were rerun after aligning to the source worker's final schemaVersion/filename contract. No live endpoint, paid call, or user browser was used; supervisor controls backend restart.


## Saved preview recovery and canvas placement

- Project load/reopen reads `GET /api/projects/{id}/visualizations` (`{jobs}`, newest 50, owner scoped) without starting a provider request. Completed results restore by `job.candidateId` or `result.lineage.candidateId`; pending jobs reconnect through the stored candidateId. Responses are ignored after account, project, or version changes.
- Only completed, non-stale results matching the current project/version and an existing candidate populate the current preview cache. An older history response cannot replace a newer in-flight or completed candidate preview. Current pending jobs are status-polled only; no generation POST is made by history recovery.
- Canvas Placement shows the newest valid current-version preview with illustrative, product-identity, physical-fit, missing-measurement and source-detail affordances. Original restores the unchanged room photo. Neither toggle starts generation. Missing/stale/history-error states explain why the original remains visible.
- All 18 mocked browser suites pass, including reload/reopen without any POST, stale-version withholding, and delayed history after project switching. A targeted history retest follows the final cache freshness adjustment. No live browser, signed-in session or provider was used.
- Export still treats every non-2xx response, including the backend's new 413 no-partial-export overflow response, as an error before reading/downloading a blob. Pagination/snapshot limitations remain the backend response's limitations metadata.


## Owner-only disclosure preview

- Client review opens an explicit selection form: product findings, saved brief notes, and individual measurements all default off. Images remain unavailable pending authorized review assets. Nothing is shared or sent, and no recipient, approval, or access grant is simulated.
- Preview selected disclosure posts `{expectedVersion, scope}` to `POST /api/projects/{id}/review-preview` and renders only the returned sanitized preview. `canCreateReview: false` is required. A changed selection clears the old result; stale versions require reload and another explicit preview. Account/project/version guards discard late responses.
- Main output uses product names, plain disclosure labels, and measurement units. Schema, raw field names, and disclosure hash are available only in collapsed advanced exact JSON. Quantity/budget approval is explicitly outside this preview.
- Both targeted mocked browser tests pass: empty defaults and exact candidate/measurement selection without private-note/location leakage; mobile stale-version recovery with explicit re-preview. The prior full run passed 19/20 with one test-only navigation locator timeout, since corrected and passing in the targeted rerun. No live browser, endpoint, or paid call was used for this work.

# Homely — end-to-end product and screen/state specification

**Version:** proposed design system, 2026-09-13. **Status:** production-oriented interaction specification for review, not an approved implementation, product validation, source contract or claim of live stock/render quality. Precedence: [CURRENT_CONTEXT.md](CURRENT_CONTEXT.md) > this proposal > dated research > historical V0 handoff. See the editable [decision flow](flows/Homely-UI-Decision-Flows-v3.drawio), [action ledger](FLOW_COVERAGE_AUDIT.md) and [image gallery](mockups/README.md).

## 0. Scope and invariants

This finite model covers **24 screen templates, nine connected multi-step journey pages, 128 supplemental named-state pages, and 370 material action branches** across mobile and laptop PWA. Most states reuse a screen template plus an explicit banner, sheet, modal or disabled action; a separate full raster for every combinatorial permutation would misrepresent the design as more resolved than it is. The gallery currently contains 12 initial concepts. The decision-flow XML and this specification define behavior independently of raster coverage. The XML is editable in draw.io/diagrams.net. All mock content is fictional. No frontend, backend or integration has been built.

Non-negotiable product rules: only exact variant and quantity with sufficiently fresh, attributable confirmation enters the **ready recommendation** lane; listing presence is not stock. Before purchase handoff, recheck and expose failure. Unconfirmed leads remain distinct. Product-in-room visualization is core, with source image/variant lineage, illustrative composite disclosure and independent measured/estimated fit. A flexible target may be exceeded explicitly; an absolute hard cap cannot. The ranking objective excludes commission. Voice can never be the only path. Consent gates camera/mic/notification access at use. The closed PWA does not itself perform reliable continuous monitoring; any permitted background checks require server infrastructure and source rights.

## 1. Actors, objects, lifecycle

**Actors:** pro designer (project owner), invited teammate, client reviewer with scoped access, DIY owner, background research worker, source verification adapter, notification service. Permissions and commercial entitlements remain proposals. A client link cannot expose private notes, unrelated projects or raw voice/photo material unless explicitly selected.

**Objects:** account and consent preferences; project and room; immutable original images and edit history; retained furniture; room measurements with unit/source/confidence; design brief with hard/soft constraints; research job and source ledger; candidate/variant and provenance; availability observation (exact variant, count, location, timestamp, method/expiry); visualization and geometry assumptions; shortlist/decision; hunt and alert policy; purchase handoff and optional affiliate attribution; earned-usage ledger. Each mutable change has actor/time/version. PII and image retention are settings, not hidden defaults.

**Lifecycles:** project `draft → active → awaiting-review → decision → completed/archived` (can return to active); job `queued → running → partial → completed`, with `paused/cancelled/failed` branches; candidate `lead → verification-pending → verified → stale/unavailable`, with variant and quantity changes forcing re-verification; render `queued → preview → validated-for-display` or `needs-input/failed`; decision `saved → proposed → approved/revision-requested → handoff → purchased-by-confirmation`, with lost-stock replacement preserving prior history; hunt `active ↔ paused → ended`; credit `pending → eligible → reserved → released/reversed` subject to actual program terms. These are conceptual statuses; do not invent guarantees from external services.

## 2. Navigation and responsive templates

Mobile tabs: Projects, Room, Explore, Saved, Account; a context voice button with visible off/listening/processing/correction state. Contextual sheets replace desktop inspector and retain back/close paths. Laptop: left project rail, center room/research canvas, right brief/evidence/decision inspector; keyboard focus and status announcement order follow visual order. At tablet widths, inspector becomes a drawer. Deep links resolve to permitted project objects and a signed-in or limited share route. Escape/back cancels a transient sheet before navigating. Every destructive action has a recoverable undo or confirmation appropriate to its permanence.

| ID | Template and canonical image | Entry / primary action | Exit / persistence | Material states and fallback |
| --- | --- | --- | --- | --- |
| S01 | Welcome / intent `13` | New user; pro or DIY intent, sign in or local preview | S02/S03; intent stored | loading, auth error, account existing, skip voice |
| S02 | Permission primer `14` | First camera/mic/notification use | S03/S04/S06; per-permission consent | denied, restricted, revoked, manual silent equivalent |
| S03 | Project home `15` | Create/open room, recent work | S04/S10/S19; project version | empty, loading, sync conflict, archived |
| S04 | Room voice canvas `01` | Capture, keep furniture, speak/edit goal | S05/S06/S07; room/history | listening, partial transcript, interrupted, denied, undo |
| S05 | Capture + dimensions `02` | Photo/import, measure table and room | S04/S06; original/measurements | camera denied, blurry, geometry unknown, offline draft |
| S06 | Style and inspiration `16` | Choose/upload inspirations, dislike/likeness | S07; taste rationale | no image, contradictory preferences, source rights |
| S07 | Editable brief `03` | Confirm intent, quantity, target/hard cap, delivery | S08; versioned constraints | ambiguous speech, invalid units, cap conflict, undo |
| S08 | Research progress `04` | Start/pause/refine/continue job | S09/S10/S19; source ledger | queued, partial, source blocked, timeout, cancelled |
| S09 | Empty/gap result `17` | Inspect no verified matches, edit only chosen constraint | S07/S08/S10; explicit relaxations | no results, source gap, stock unknown, offline stale |
| S10 | Findings `05` | Listen/read briefing, expand three example choices | S11/S12/S14; candidate set | verified, stale, partial coverage, unconfirmed separate |
| S11 | Candidate evidence `06` | Inspect exact variant, count, dimensions, source, cost | S12/S13/S14/S16; evidence timestamp | variant mismatch, quantity short, unknown, expired |
| S12 | Unconfirmed lead `18` | Investigate/ask seller/save without ready badge | S11/S19; inquiry history | pending, inaccessible, rejected, manually confirmed only with evidence |
| S13 | Product in room `07` | Original/composite/measurements, swap item | S11/S14; composite lineage | render pending, identity uncertainty, geometry unknown, failure |
| S14 | Mobile compare `19` | Side-by-side tradeoffs, adjust target/cap, select | S11/S16; comparison version | missing cost, cap exclusion, all options gone |
| S15 | Desktop project canvas `10` | Plan room, measurements, brief, voice shortcut | S08/S20; same project model | syncing, image missing, measurement estimates |
| S16 | Decision/budget `09` | Save/share, recheck, open seller | S17/S20/S21; decision ledger | price change, over cap, stock lost, checkout external |
| S17 | Handoff + credits `20` | Open seller only after recheck, disclose referral | S16/S21; attribution if eligible | canceled, return, commission unknown/reversed; no assumed purchase |
| S18 | Hunt stock change `08` | Alert on meaningful new/lost match, compare replacement | S11/S16/S19; activity history | notification denied, source suspended, duplicate alert |
| S19 | Saved hunts + inbox `21` | Resume/pause/cadence/source scope | S08/S18; preferences/history | empty, no push, stale, paused, background source gap |
| S20 | Pro client review `12` | Share scope, comment, approve/request changes | S16/S21; actor/time/version | expired link, revoked access, divergent revision, lost stock |
| S21 | Purchase/decision ledger `22` | Mark purchased explicitly, log receipt/status | S03/S19; decision/proof | not purchased, canceled/refunded, external order unknown |
| S22 | Account/privacy `23` | Consent, retention, export/delete, alerts, billing | S01/S03; user settings | export queued/error, delete confirmation, revoked permission |
| S23 | Offline/sync conflict `24` | Inspect cached data/queued edit and reconcile | Return to source template; conflict resolution | offline stale stock, queued noncommerce edit, version conflict |
| S24 | Desktop research/compare `11` | Source ledger, evidence matrix, three-way tradeoffs | S11/S13/S20; same candidate model | partial sources, expired stock, unconfirmed lane |

`01`–`12` are current gallery filenames; `13`–`24` are planned screen images; mobile/desktop are representative compositions, not separate behavioral silos. S20's image `12` is a laptop client view. Some templates (S04, S05, S07, S08, S10, S11, S13, S16, S18) use initial concept images; further screen and failure-state raster concepts are outstanding. The mockups are not literal pixel acceptance criteria: generated dates, stock claims and product details can be inconsistent. This specification controls behavior.

## 3. State patterns and transition contracts

Each screen follows a shared contract: `idle → loading → success | empty | recoverable error | permission-needed | offline-stale`; loading does not erase last known evidence, and the last checked time remains visible. A failed action offers Retry and a safe route back. Sheets/modal focus is trapped and restored to invoker. Toasts announce reversible changes with Undo. A spoken command first updates a provisional transcript/parsed intent; only committed constraints start a new research version. Status chips are text, icon and color.

### Auth, onboarding, permissions (F01)

S01 allows pro, DIY and preview entry. Explain pro collaboration separately from future DIY packaging; do not force a commercial commitment. Sign-in failure preserves unsent brief. Camera consent is requested from S05, microphone from S04, push from S19 after a hunt is saved. S02 can show denied and settings-help states; manual photo upload and silent controls remain complete. Consent changes are audited; a revoked mic immediately stops capture. There is no background always-listening default.

### Projects, room, retained pieces and dimensions (F02)

S03 creates a named project; S04/S05 accept one or multiple original images and annotate an existing table as Keep. Mark a dimension `measured`, `user-estimated` or `AI-estimated` with units and source. Ask for table underside height and chair quantity before asserting arm clearance. Missing measurements can proceed with uncertainty but cannot be represented as validated physical fit. Photo upload failure keeps local draft; deletion offers restore until permanent purge confirmation. Laptop S15 edits the same version; concurrent edits route to S23.

### Voice lifecycle and silent equivalence (F03)

Button states: `off → permission primer → listening → provisional transcript → parsing → proposed change → committed`, with `stop`, `interrupt`, `correct`, `undo`, `timeout`, `denied` branches. Voice says what changed in brief/room/hunt; screen highlights exact chips/objects. A misheard “six” or $2,400 is corrected before job submission. Processing can be canceled. Spoken briefings have playback, captions and mute; no auto-playing voice for screen-reader users by default. All actions have UI and keyboard paths.

### Taste, brief, budget (F04)

S06 uses inspirations, disliked materials and preserved pieces; users may see and remove inferred taste labels. S07 distinguishes preferences from hard constraints. Validate positive quantity, compatible dimensions and feasible location. When target exceeds hard cap, ask which number to edit; never silently raise cap. Changing budget invalidates comparisons and may restart research with a new version, preserving prior results as history.

### Research and source lifecycle (F05)

S08 records job ID, source set, query version, geographic scope and each source's `not-started/checking/checked/blocked/failed/stale`. A partial briefing explicitly lists missing sources. S09 explains no verified match and offers edits chosen by user, not automatically relaxed limits. Pause stops new scheduled checks as feasible; in-flight calls and queued alerts may need explicit cancellation semantics. Closed/browser-offline PWA cannot monitor itself; source-lawful backend jobs, costs and push support are validation dependencies. No Facebook Marketplace/Craigslist direct access is promised; eBay is conditional on approvals/terms.

### Candidate, variant, stock and replacement (F06)

S11 requires source URL/evidence, product identity, finish/size, exact variant, required quantity, location, delivery method and timestamp. Verification policy/expiry is source-specific and must be validated; UI never turns “live listing” into confirmed count. Price and delivery evidence are separate. Recheck before handoff; failures move candidate out of ready lane and S18 records lost-stock event. Saved decision remains historically visible, never silently substituted. S12 hosts seller-contact or manual leads with visible uncertainty. A substitute must compare changed look, dimensions, condition, delivery and all-in cost.

### Visualization and physical fit (F07)

S13 records original room image, source product images, exact variant, geometry version, renderer version and timestamp. The original and source image remain accessible. A generated composite is labeled illustrative. Use measurements to check seat/arm/table underside, circulation and scale; an image is not proof. Unknown floor plane, occlusion or absent exact finish requires a `needs input`/low-confidence state and a specific measurement request. Render/rights failure falls back to source photo plus dimensional evidence. No fictional asset can be presented as the real SKU.

### Comparison, decision and cost (F08)

S10/S14/S24 compare best fit, within flexible target and savings as suggested lanes, with expandable full search. Total delivered cost includes product, shipping/pickup, taxes, fees, restoration/assembly as relevant, estimated components tagged. A hard cap excludes an item even if visually attractive. Flexible target premium shows $ and %. A selection snapshots evidence and budget version. S16 triggers a fresh variant/quantity/price check before external seller handoff. A click is not a purchase.

### Saved hunts and alerts (F09)

S19 sets source set, geo radius, category, cadence, quiet hours, pause/end and notification channel. S18 groups repeated changes, explains why a new find matters and exposes source/check time; losing six-unit availability is actionable. Push denied still leaves in-app activity. Alerts link to evidence with a recheck, not a guaranteed purchase. Do not bill or award usage for hidden monitoring without an explicit model and bounds.

### Pro client review and revisions (F10)

S20 creates a scoped, revocable approval view with selected room composite labeled illustrative, measurements, stock/cost freshness, alternatives, notes and client comments. Preview exactly what the client sees. Approval locks a variant/version, but does not reserve stock or authorize purchase. Requested changes return to S07/S08 while keeping decision history. Revocation blocks future access; copies already exported are not magically revoked. Teammate/client roles and invitations need permission tests.

### Purchase, affiliate, earned usage (F11)

S17 performs fresh check and opens the seller; return flow asks user to mark purchased, canceled or still considering. Affiliate attribution exists only for contracted eligible links. Commission is pending until realized; returns/refunds reverse it, reserve is held, credit issued within cost limits and allowed program incentives. S21 shows ledger and status, not invented transaction settlement. Ranking never uses commission, and marketplaces without contracts earn no presumed commission. Paid pro, DIY pass, free affiliate and hybrid remain experiments.

### Account, privacy, offline and cross-device (F12–F14)

S22 manages project data, voice transcript/recording retention, photo permissions, export, deletion, notifications and billing transparently. Export can queue; permanent purge requires explicit confirmation at action time. S23 marks cached evidence stale and disables live stock claims/handoff offline. Queue only safe edits and reconcile by version on reconnect. Concurrent edits present both actor/timestamp versions with merge/restore. Web push, camera capture, background sync, storage quotas and microphone behavior vary by browser/OS; validate on target iOS/Android/laptop browsers and offer visible fallback. Accessibility test coverage includes keyboard, VoiceOver/TalkBack, text zoom, reduced motion and color-independent status.

## 4. Journey coverage and acceptance conditions

| Journey | Path | Success condition | Key alternate/recovery |
| --- | --- | --- | --- |
| J01 First pro project | S01→S03→S04→S05→S07 | Existing table, quantity, target/cap and room saved | S02 denied → manual/silent |
| J02 DIY first project | S01→S03→S04→S06→S07 | Accessible guided brief without pro jargon | Skip voice, no photo, estimated room |
| J03 Voice correction | S04→S07 | Corrected fields highlighted and reversible | Interrupt/cancel/permission revoked |
| J04 Research | S07→S08→S10 | Source ledger, honest partial status, verified ready cards | S09 no results/source gap; pause/resume |
| J05 Local secondhand lead | S08→S12→S11 | Confirmation method evident before ready lane | Inaccessible listing remains lead |
| J06 Room visualization | S11→S13→S14 | Exact variant lineage and separate geometry confidence | Render/rights/measurement failure fallback |
| J07 Compare and choose | S10→S14→S16 | Hard cap respected, all-in cost and tradeoffs | Missing delivery costs block certainty |
| J08 Stock disappears | S16→S18→S11 | Prior choice retained, replacement difference explained | No verified replacement → S09/hunt |
| J09 Persistent hunt | S08→S19→S18 | Meaningful checked change and alert control | Push denied, backend/source paused |
| J10 Client decision | S16→S20→S21 | Scoped review, actor/time/version and recheck | Revision/revocation/expired link |
| J11 Purchase and usage | S16→S17→S21 | External handoff distinct from purchase; eligible credit ledger | Return reversal, no affiliate agreement |
| J12 Offline/multi-device | Any→S23→source | Stale data clear, safe edits reconciled | Conflict, quota, unsupported push |
| J13 Privacy lifecycle | S03→S22→S03/S01 | Export/retention/deletion controls | Export fail, revoke permission |
| J14 Laptop deep review | S03→S15→S24→S20 | Same data/version, evidence-rich comparison | Cross-device conflict → S23 |

Acceptance tests should be behaviorally meaningful: exact-variant/quantity stock gate never admits a listing-only lead; cap remains hard through comparison and rerank; failed recheck blocks ready handoff; generated composite never claims dimensional proof; voice cancellation leaves prior state; offline price/stock is stale; pro sharing shows only scoped content; commission does not alter ranking; alert on lost stock preserves history. Visual accuracy needs empirical tests with actual products/rooms, not screenshot resemblance. Source, legal, accessibility, privacy and platform compatibility gates precede launch.

## 5. Decisions still required before build

Target initial professional job and measurable success threshold; approved source/data/image rights and verification method; freshness SLA by source/category; fidelity threshold and render strategy; room measurement protocol; privacy/retention defaults; pro/client role scopes; onboarding and voice setting defaults; background monitoring frequency/cost; notification and offline support by platform; monetization and affiliate program terms. The five candidate alternatives, example prices and screenshots do not settle these. Design review should establish the interaction model and screen hierarchy first, then validate specific engineering capabilities and commercial feasibility.

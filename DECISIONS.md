# Current ownership correction

2026-09-13: Task 01a09cd5-ead3-7530-9d67-305074926e94 completes turns without any executed items and is idle/read-only. Task 01a09c11-8332-7352-9900-0b1e83b55bab retains sole implementation ownership. Transfer notes below are historical; do not start another writer. Active workers: sourcing owns backend/assistant.py and its tests; interface owns web main app/tests; ux_review performs read-only live regression. Supervisor owns server/cloud integration and canonical logs.

# Homely implementation decisions

Updated: 2026-09-13. Owner: integration supervisor.

- **Stack for first integrated POC:** dependency-light Python standard-library HTTP server plus responsive vanilla HTML/CSS/JS. This makes a working local preview available quickly, keeps API keys server-side, and avoids dependency installation as a blocking step. Modules can later migrate behind the same HTTP contract.
- **Truth:** candidates default to `lead`. A ready label requires attributable exact variant, quantity and freshness evidence; a web-search result alone never qualifies. Handoff rechecks evidence and hard cap.
- **Visualization:** user-provided original room and product source images; generated composites are illustrative and require explicit provenance. Numeric fit is separate. Missing consent/rights/measurements returns a visible need-input state.
- **Persistence:** app-owned local JSON/files for the POC, with versioned project mutations and server-only `.env.local`. No provider session is canonical storage.
- **Concurrent files:** interface owns only `web/`, sourcing owns `backend/sourcing.py` and `backend/tests/test_sourcing.py`, visualization owns `backend/visualization.py` and `backend/tests/test_visualization.py`; supervisor owns other files and integrates.
- **Development model:** GPT-6 Astra with medium reasoning is the user-requested coding/supervision model; implementation workers were spawned explicitly with that setting. This does not choose Homely runtime models.
- **Approved visual target:** all twelve actual PNGs already stored in `docs/product-context/mockups/` are the accepted UI reference, especially 01 mobile room/voice, 03 brief, 05 findings, 07 visualization, 10 desktop canvas, 11 research/compare and 12 client review. Compare running screenshots and correct obvious drift.
- **Public page extraction in first iteration:** after source-cited OpenAI web discovery, the server may safely fetch public product URLs. Generic Product/Offer JSON-LD, supported structured data and conservative metadata extraction carry field-level provenance. Fetches obey robots, DNS/redirect/public-IP checks, host throttle, time and byte caps. Unknown variant/quantity/fulfillment stays unknown; public HTML is not a stock adapter.
- **Pending capability UI:** planned affordances remain visible and disclose 'not available yet' without fake success or losing entered data. Working core actions remain real.

- **New supervisor:** implementation transfers to task 01a09cd5-ead3-7530-9d67-305074926e94 in the requested repository. Prior agents are completed; no duplicate writers. HANDOFF.md records continuity.
- **Cloud POC requirement:** existing FREE Supabase project bbwmwwupvqajidqznsly for real Auth, DB and private assets; no paid changes. Local data remains intact until explicit user-selected migration. Live cross-user isolation is required for POC acceptance.
- **Conversational POC requirement:** both typed messages and push-to-talk voice must invoke grounded, authorized app actions through one server routing path, with correction/confirmation and honest action state. Placeholder voice UI does not satisfy it.
- **Progress:** weighted acceptance checklist, separate POC/production denominator; report scope changes and never translate percentage into promised time.

## September 17 — repeatable designer dining-chair test fixture
Professional designers and dining-chair replacement are the current test priority. Fixture uses real public product links, keeps unverified stock/cost/fit explicit, and isolates all fictional project data from existing local/cloud workspaces. Photo-display permission does not stand in for external AI processing consent. Independent text sourcing/import need not be blocked by room-image rights; fixture launcher disables paid provider calls by default.

## September17 — Room view scope and truthful reference adaptation
The supplied mobile mockup is the Room view inside a selected project, not the global homepage. Explore shows that project's findings; Saved shows its decisions. Match the reference's layout/style while retaining the actual project photo/data. Idle voice must not mimic recording; Keep opens retained notes until real object anchoring exists. Additional supported photo/placement/research controls remain accessible.

## September17 — approved progressive onboarding supersedes earlier Room layouts
The user-approved reference is mockups/13-approved-room-flow.png. Implement room choice, then setup as consecutive interactive screens. Generic room imagery is illustrative; retained pieces are explicitly named notes, never detected objects. Latest user direction: use generic room inspiration in setup even when a project has an uploaded photo, while preserving the actual original in expandable project details/canvas. No data replacement.

## Fit-qualified recommendations — firm requirement; next mockup pending approval
Only recommend a product as fitting retained furniture when its applicable measured constraints have been validated. This supersedes any skip-measurements-and-recommend assumption. Missing, conflicting, or insufficient dimensions block fit-qualified results; saving and resuming later must remain available. Optional inspiration browsing is a separate, clearly labelled experience and must never be described as fitting recommendations.

The fit gate requires the user's confirmation of the retained object and exact variant, measured or traceable retained-object dimensions, candidate-specific dimensions for the exact candidate variant, and deterministic geometric constraints with explicit clearance tolerances and supporting evidence. Keep units, measurement/source provenance and unresolved uncertainty visible. Conflicting sources require resolution; do not silently select a favourable value or substitute photo estimates for measurements.

For dining chairs, validate arm clearance beneath the lowest relevant table edge/apron, seat-to-table relation, chair width against table leg spacing, and the requested chair count/arrangement and usable clearance as applicable. Height alone does not establish universal fit. Any fit statement is limited to the measured constraints actually validated; do not promise an absolute guarantee beyond that evidence.

Add this measurement gate before fit-qualified results in the next design/spec, including an explanation of what is missing, source uncertainty handling, and graceful save/resume. The revised flow still awaits final mockup approval. This records a requirement only; no new implementation is authorized before that approval, and existing code must not be represented as already satisfying the expanded gate.

## Nine-step flow approved — implementation authorized
The user explicitly approved mockups/14-approved-nine-step-flow.png and authorized implementation. This resolves the previous approval gate. The strict fit requirements remain binding. Build progressive save/resume with optional photo/measurements, explicit retained-object confirmation, personalized categories, a fit gate, separate inspiration, and separate product saving/opt-in price watching. No automatic paid calls or unapproved services. Photo anchors are user-confirmed annotations, not automatic object recognition or measured geometry. A local scheduled watch must disclose server availability and in-app delivery limits.

### Explicit recovery and price-watch authorization
After explanation of password-recovery security and source-price/failure risks and scope limits, the user explicitly said “Yeah, sure, let’s I approve it.” This fresh authorization covers implementing password recovery/password-update handling and product-opt-in scheduled public-page price checks with in-app notifications. It does not authorize changing the actual user's password, sending recovery mail during tests, activating a watch without product-specific opt-in, or paid services. Resume implementation through normal approval review; report any remaining rejection without workaround.

# Homely — product experience and UI/UX concept

**Status:** proposal for Linnea's review, 2026-09-13. This is a design brief and five-screen concept, not approved product scope, implemented UI, live source access, verified inventory or proof of rendering fidelity. Read [current decisions](CURRENT_CONTEXT.md) and the [source index](INDEX.md) first. Firm requirements in that record take precedence over design suggestions here.

## Product thesis

Homely is a personal AI interior design partner for an actual room and an evolving project. It understands the pieces a person owns, the feeling they want, spatial and practical constraints, budget, and what has already been considered. It researches distinctive new, vintage and secondhand options, checks whether an exact usable item is available, places that actual item in the room with honest visual and dimensional evidence, and helps people decide. Start with professional designers, then test a DIY version that makes this expertise approachable. The intended convenience comes from work Homely completes between interactions, not from making a user formulate clever prompts.

**Primary interaction:** voice on mobile, accompanied by direct manipulation of room photos, product cards, dimension markers, filters and comparisons. Every voice action has a visible, reversible result; every task works silently by touch, pointer and keyboard. The assistant is present in the workspace, not a scrolling chat transcript. A laptop PWA offers the same project memory with more space for planning, review and client collaboration.

**Differentiation hypothesis:** Vendora already explores designer-brief sourcing; Decato addresses room fit, visual design and live IKEA/Wayfair shopping on the checked page; Fringe offers supplier-funded free discovery; SPEKD explains source-grounded matches; Studio Designer owns procurement workflow; Onton and Spoken support visual discovery and price comparison; Swoopa and Aggario monitor listings. Homely must prove the combination of room-aware judgment, wide distinctive new/used sourcing, exact availability, faithful real-product visualization and persistent collaborative refinement. None of these individual capabilities is unique by assertion. A September 13 check of [Decato’s software](https://decato.ai/software) and [about](https://decato.ai/about) pages found an advertised end-to-end floorplan → real in-stock furniture → fit/budget → render → spec/deck workflow, with Mac and IKEA/Wayfair described as live on its [team page](https://decato.ai/team). Thus “integrated room-to-shopping” by itself is not a defensible distinction. Among the reviewed companies no exact full combination was verified, which is not proof that none exists. [Studio Designer reports](https://www.studiodesigner.com/about-studio-designer/) 20,000+ users and $5B annual orders; orders are not its revenue and users are not verified paid accounts. [Vendora](https://www.sourcevendora.com) remains early access with no public paying count; [Fringe’s supplier page](https://www.fringeinterior.com/for-suppliers) reports reach/activity, not a verified paid-customer count. Homely’s possible voice/mobile, distinctive cross-source/secondhand and ongoing personal-research edge still needs validation. The product should be benchmarked on successful decisions and time saved, rather than impressive-sounding AI output. The founder's 60% sourcing-time estimate remains a hypothesis.

## Experience principles

1. **The room is the canvas.** Show the real room, retained pieces and chosen product before a text-heavy summary. Preserve the distinction between an original photo, a product source image, a generated composite and measured geometry.
2. **Speak, see, correct.** Keep spoken turns short; show the interpreted brief and changed constraints immediately, with Undo/Edit. Allow interruption and correction in natural language or controls.
3. **A recommendation is actionable evidence.** State exact variant, required quantity, location, source, last verification and total delivered cost. Unknown availability belongs in a separate lead lane.
4. **Good taste meets physics.** Explain aesthetic compatibility alongside seat/arm height, clearances, size, condition, delivery and uncertainty. A beautiful image never substitutes for measurements.
5. **Show meaningful options.** Begin with best fit, within target and savings as an illustrative comparison, with an expandable search. Respect an absolute cap; show the precise premium over a flexible target.
6. **Make ongoing work legible.** A saved hunt shows what sources were checked, when, what changed, and why an alert matters. No fake “live” promise where access is unavailable.
7. **Earn trust in incentives.** Ranking stays independent of affiliate commissions. Explain any eligible earned usage and returns reserve without nudging toward commission-paying items.
8. **Progressive disclosure.** A novice can start with a photograph and spoken goal; a professional can inspect evidence, dimensions, sourcing provenance and client-ready comparisons.

## Information architecture

| Area | Purpose | Mobile | Laptop |
| --- | --- | --- | --- |
| Projects | Rooms, briefs, retained items, budget, collaborators, status | Home cards and focused room | Project rail and canvas |
| Room | Original/captured photos, calibrated dimensions, geometry uncertainty, visual variants | Full-bleed image and overlays | Large canvas plus object layers |
| Research | Active search, checked sources, leads, verified recommendations, saved hunts | Briefing cards and filters | Search/evidence workspace |
| Compare | Fit, true cost, stock, visual swaps, tradeoffs | Swipe/stack and side-by-side toggle | Matrix with room and shortlist |
| Decisions | Saved, rejected, client approval, purchased and replacement | Status chips and activity | Decision ledger and exports |
| Account | Permissions, voice, alerts, privacy, projects, billing/credits | Profile/settings | Workspace settings |

A project owns rooms and design goals. A room owns a measured-or-estimated geometry model and immutable original photographs. A sourcing brief can span rooms. A product candidate has source evidence, variant, stock/quantity status and timestamp; a visualization has lineage to that exact candidate, photo and geometric assumptions. A decision records who approved what and when. This model supports cross-device continuation without presenting the assistant as an endless conversation.

## Feature and function inventory

| Capability | Initial experience proposal | Later or unresolved |
| --- | --- | --- |
| Voice and silent control | Push-to-talk or explicit listening state; live transcript preview, correction, interruption, mute, undo; touch/keyboard equivalent | Hands-free wake behavior, background voice and native integration need privacy/platform tests |
| Onboarding | Choose pro/DIY intent, create first project, explain photo/mic access at point of use, start silently | Pricing/organization defaults need interviews |
| Room capture | Mobile camera/import, multiple viewpoints, mark retained items, guided dimensions and confidence labels | Automated geometry/AR precision requires validation |
| Brief and taste | Voice or form for goals, dislikes, constraints, inspiration, target vs hard cap; editable structured chips | Taste memory personalization needs consent and tests |
| Sources and research | Licensed/allowed retailer feeds and accessible sources, explicit source coverage/freshness; separate unverified leads | Marketplace/Craigslist integration and continuous monitoring not assumed; eBay subject to approvals and terms |
| Candidate evidence | Exact variant, quantity, condition, location, stock evidence and recheck; delivery costs | Direct seller confirmation and checkout integration depend on source rights |
| Visualization | Real-item room composite with source identity, material/color, perspective and scale confidence; swap options | “Perfect” fidelity is a research goal; geometry and imagery rights unresolved |
| Comparison | Best fit / within target / savings, hard-cap exclusion, all-in cost and tradeoffs; expand results | Dynamic optimization across rooms and procurement later |
| Hunts | Save search, backend checks where permitted, change log, meaningful alerts, replacement of lost items | Monitoring frequency, source access, cost and alert quality need tests |
| Collaboration | Designer/client roles, share shortlist, comments, approve/reject, audit trail | Purchase orders, vendor management and integrations later |
| Commerce | Purchase link only after recheck; no false order confirmation; record purchased status | Affiliate contracts, project pass, pro seat and hybrid are commercial tests, not decisions |
| Memory | Project-scoped preferences, corrections, decisions, retained pieces; visible edit/delete | Cross-project personalization and retention policy need consent decisions |

## Screen architecture and responsive behavior

**Mobile PWA:** bottom navigation for Projects, Room, Explore and Saved; persistent compact voice button whose state is explicit. Photograph occupies the upper half when room-focused. A bottom sheet displays one immediate decision at a time and can expand for evidence. Large targets, one-handed actions, captions and reduced-motion transitions. Camera and photos are requested only when entering capture. Voice is optional from first launch.

**Laptop PWA:** left project/room rail, central photograph or comparison canvas, right contextual inspector. The rail collapses; central canvas can show an original/photo/composite toggle, dimension overlays and product swaps. The inspector hosts brief, stock evidence, budget and sources. Voice remains a useful shortcut with equivalent keyboard/GUI. At intermediate widths, inspector becomes a drawer; no workflow requires hover. Saved edits and research sync between devices with clear last-updated/conflict state.

**Shared visual language (proposal):** warm off-white `#F6F3ED`, ink `#1F2925`, forest `#285449`, soft sage `#DDE8DC`, restrained copper `#C87858`, line `#D7D9D1`; candid interiors rather than generic AI gradients. A humanist display serif for room/project titles and highly legible sans-serif for controls and data. Status uses words and icons plus color: “Verified 2:14 PM,” “Needs confirmation,” “Unavailable.” Spacious photography with dense evidence only on expansion. Accessibility contrast is verified in implementation, not presumed from this palette.

## End-to-end flows and states

### 1. Start a room and describe the job

A designer creates “Maya's dining room” on mobile, captures/imports a room photograph and marks an existing walnut table to keep. The app asks for only missing essentials: table top/underside height, chair clearance, seating count, room dimensions or confidence that measurements are estimates. Voice: “Find six chairs that work with this table, warm but not matchy, ideally under $2,400 delivered.” A live transcript preview lets the designer correct “six” or the price before submitting. The structured brief reveals inferred style, quantity, target, absolute cap (if supplied), location, timing and condition preferences. Each is editable and Undo restores the prior state. The laptop shows the same room and brief for more deliberate review.

If photo permission is denied, upload or enter room dimensions manually. If microphone permission is denied, the app offers the same structured entry, without blocking. Never start recording without a visible state and stop control. Ask before storing voice recordings; transcript retention and deletion are explicit preferences.

### 2. Research and a useful briefing

Research shows a progress ledger: accessible sources searched, exclusions, stale feeds, independent/vintage coverage and remaining checks. This is source-specific evidence, not a theatrical spinner. When ready, a short optional spoken briefing says what was found and the critical tradeoff; the screen shows best fit, within target and savings. The first may exceed a flexible target with exact dollars and percent, but never a hard cap. Each card shows product/source image, exact variant, quantity, stock verification timestamp, aesthetic and dimensional fit, all-in delivered cost, condition and next action. Expand for underlying URLs, fit evidence and uncertainties. The user can say “show something lighter and local” or adjust the visible filters; the changed brief and research delta are visible.

If no verified option meets the brief, explain which constraints bind, show safe relaxations for user choice, and retain unverified leads separately. If a source is inaccessible, say so and offer lawful saved/manual options. Do not infer stock from a listing's existence. A fresh listing with uncertain quantity remains a lead until seller/source confirmation supports exact item and quantity.

### 3. See the actual choice in the room

Tapping a verified chair opens the room visualization with the selected exact product/finish/variant and quantity. Toggle “Original photo,” “Illustrative placement” and “Dimensions & evidence.” The composite should preserve silhouette, materials/color and plausible perspective; show a confidence disclosure and source photo. Known measurements drive seat, arm, footprint and passageway checks. Unknown floor plane, occlusions or missing dimensions are labeled, with a prompt to measure rather than fabricated certainty. Swap the next alternative while keeping the room view steady; compare visual differences. Exported images carry product/variant attribution, timestamp and an illustrative-composite label.

If rendering fails, keep the original room/photo, product images and dimensional comparison available; do not hide the recommendation. If exact finish photos are absent, no photoreal-looking substitute should claim to depict the product. “Perfect real product” remains a quality target that must be tested using real merchant assets and measured rooms.

### 4. Decide, share and continue

The pro can save, reject with a reason, request a replacement, or send a client an approval view with budget and evidence. Approval records the variant and timestamp, then availability and total cost are rechecked before the purchase link. If stock is lost or quantity drops, label the prior card unavailable, preserve the decision history, propose a closest replacement and explain changes in size, look and total cost. A purchased item is marked only by user action or a confirmed integration, not inferred from a click. A saved hunt can continue allowed checks and alert only on high-fit changes; users control cadence, pause and source/location scope. DIY uses the same core decision path with less professional terminology and no assumed procurement obligations.

### 5. Price and incentives

Show actual fees before use. Commercial candidates—pro seat, one-project DIY pass, affiliate-supported free and hybrid—remain separate experiments. When applicable, earned credits appear only for eligible attributable commissions after fulfillment and a return reserve, bounded by service cost and allowed program terms. A product card never implies a commission because a marketplace listing may have none. An explanation page states ranking uses fit, availability, cost and user constraints, independent of commission.

## Failure, permission and offline states

| State | User-facing behavior |
| --- | --- |
| Speech unclear/interrupted | Show partial transcript, ask for the ambiguous field, preserve previous constraints and allow undo. |
| Camera/mic denied | Silent/photo-upload and form path remains complete; no nag loop. |
| Source timeout/terms limitation | Mark source and last successful check; do not claim exhaustive coverage or secretly scrape. |
| Exact stock unknown, wrong variant, quantity short | Move to “Needs confirmation” leads; never place in verified shortlist. |
| Stock changes during review | Warning, timestamp, recheck, replacement alternatives; approval history retained. |
| Dimensions or render uncertain | Show measured/estimated distinction and source image; prompt for a specific missing measurement. |
| No matches within hard cap | State why, allow explicit constraint edit; never quietly overrun cap. |
| Offline PWA | Cached rooms/notes and previously viewed cards clearly marked stale; queue local edits where safe, reconcile conflicts on reconnect. No live stock/price or source checks while offline. |
| Notification blocked | Saved-hunt activity remains in-app; explain that push alerts need permission. Background monitoring, if authorized and viable, runs on a server, not from a closed browser tab. |
| Data sync conflict | Show two versions with author/time and merge/restore; do not silently overwrite another designer's work. |

## Accessibility and privacy

All voice actions have equivalent labeled controls, visible focus order, keyboard shortcuts, captions/transcripts and screen-reader announcements for status changes. Give users time to inspect the transcript and cancel. Respect reduced motion, pinch zoom on imagery, text scaling and color-independent statuses. Do not rely on an image to convey fit or inventory facts. Ask for camera, mic and notifications at the moment of use; explain purpose and storage. Distinguish client/private project material from sharable approval views. Provide retention, export and deletion controls for photos, transcripts and project memory. External product imagery and room photos require appropriate rights and privacy handling.

## Evidence, metrics and validation experiments

Instrument consented events for time from brief to verified decision, fraction of candidates with exact variant/quantity confirmation, stale-stock rate, false “available” rate, successful purchase/link follow-through, fit rejections, visualization identity/scale error, research alert precision, replacements, pro time saved, client approval time, DIY completion, repeat use and contribution after AI, source and human verification cost. Avoid treating registration or gross merchandise value as product-market fit. Segment by source, geography, category, professional vs DIY and measured vs estimated room geometry.

Test with designers on real chair/table and other constrained rooms; compare native retailer search, marketplace alerts, Vendora/Decato where accessible and existing workflow. Blindly judge selection quality and whether a decision could be made from evidence. Run seller/source access and freshness pilots; separately validate real-product room compositing against product photos, known dimensions and physical placements. Interview and price-test both audiences before selecting monetization. Low/medium/high, TAM/SAM/SOM and marketing budgets in the [business plan](research/AI-Furniture-App-Business-Plan.md) are conditional inputs for these experiments, not operating forecasts.

## Preliminary mockup coverage and review questions

The [five concept screens](mockups/README.md) tell one illustrative dining-chair story. All photos, products, prices, stock times and names shown are fictional UI content; the visuals are design references, not functioning software or proof of actual-product rendering. They cover: mobile room/voice; mobile verified research; mobile product-in-room swap; laptop project canvas; laptop evidence-rich comparison. The visual language and content density should be reviewed before extending into exhaustive states or implementation.

For Linnea's review: Does the workspace feel like an intelligent design partner rather than a chat app? Is voice genuinely convenient without obscuring direct control? Do verified stock, actual-product fidelity and fit evidence feel central? Is the mobile/laptop division useful to both a working designer and a future DIY customer? Which visual direction or interaction should change before full mockups?

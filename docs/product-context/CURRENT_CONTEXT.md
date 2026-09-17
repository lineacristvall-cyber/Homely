# Homely: current product context and decisions

Read this first. It records decisions from the product conversation after the older Codex handoff and after the September 2026 desk-research report. The source files remain unchanged in [`research/`](research/) and [`historical-handoff/`](historical-handoff/). The [document index](INDEX.md) inventories every preserved file. This is a decision record, not a claim of empirical validation or an instruction to build immediately.

## Vision and audience

Linnea is the core visionary. Homely is an ambitious AI interior design partner that combines intelligence with easy convenience. Start by serving professional interior designers; later make comparable help accessible to DIY users. It should understand a person's room, retained furniture, aesthetic, dimensions, practical constraints, and project history. Work collaboratively: explore directions, explain tradeoffs, remember feedback, refine alternatives, and continue useful research over time. It is more than a crawler, a fixed five-result catalog, or a quick proof of concept.

A concrete example is finding chairs for a table the customer owns: account for seat and arm heights, dimensions, quantity, visual scale, room style, all-in price, delivery, and condition. Seek distinctive as well as familiar options. West Elm and CB2 are not banned, but defaulting only to generic large retailers misses the ambition. Explore independent and vintage sources, new and secondhand local inventory, including desired Facebook Marketplace, Craigslist, and eBay opportunities. Access, lawful integrations, freshness, and feasible monitoring for these sources are unresolved; an advertised listing is not guaranteed inventory.

## Firm core requirements added after the report

1. **Verified availability.** Ready-to-act recommendations contain only the exact product variant and needed quantity actually available/in stock, with a verification time and an appropriate recheck before action. A live marketplace listing alone is not confirmed stock. Uncertain leads may be shown distinctly as research leads, never mislabeled as ready recommendations. This strengthens the older handoff's product-truth rule.
2. **Faithful actual-product-in-room visualization.** Visualization of a specific real product in the user's room is core, and option swaps must update the scene. Preserve the product's identity, silhouette, material/color, and plausible scale/perspective. “Perfect” fidelity is an aspiration to validate technically, not a capability already proven. Generative imagery alone does not verify physical dimensions or fit. The old handoff and report's no-render/deferred-render assumptions are superseded.

A design direction can show three illustrative alternatives: strongest overall fit (possibly above a **flexible target** with the dollar and percentage premium and a reason), within target, and cheaper with transparent compromises. A **hard spending cap** is absolute; compare total delivered cost, including relevant taxes, shipping, pickup, restoration, and fees. This is an explanatory comparison, not a fixed result count or interface limit.

## What is still being decided

The US is a working launch assumption, not a final geography commitment. The initial designer workflow, source coverage, monitoring cadence, verification protocol, visualization approach and measurable fidelity standard need validation. Voice, camera, and native delivery are not finally excluded. Privacy and licensing for room images, merchant images and marketplace data need design. Do not assume source access or affiliate rights: Facebook Marketplace and Craigslist integrations/continuous monitoring require investigation; eBay access, approvals and terms govern any use.

The monetization candidates are paid professional seats, DIY project passes, free affiliate-supported usage, and a hybrid. None has been chosen. Any “purchase funds usage” flywheel must issue cost-limited earned credits only after eligible, attributable, realized commissions, with returns reserve and program incentive approval. Never rank products by commission, and do not assume affiliate proceeds from uncontracted marketplaces. Professional and consumer acquisition, conversion, service cost, repeat behavior, and viral reach in the research are conditional scenarios. Annualized ending-seat run rates are not realized annual revenue.

## Evidence standard and competition

The preserved work is desk research: it does not include designer interviews, hands-on competitor benchmarks, contracted source access, or proven product fidelity. The founder's “60% of a designer's time spent sourcing” is a hypothesis, not a verified population fact. Market size and low/mid/high projections are estimates with explicit inputs and sensitivities, not forecasts. See the [business plan](research/AI-Furniture-App-Business-Plan.md), [interactive research report](research/interior-design-business-report.html), and underlying [market](research/furniture-market-sizing.md), [business-model](research/furniture-business-model.md), and [competition](research/furniture-competition-research.md) memos for assumptions and citations.

Vendora is a close professional brief-sourcing concept; Decato is close to integrated room-fit/visual sourcing (IKEA/Wayfair were live on the checked page; other integrations were planned). Fringe offers supplier-funded free discovery, SPEKD evidence-grounded sourcing, Studio Designer mature workflow/procurement, Onton and Spoken visual discovery/price comparison, and Swoopa and Aggario monitoring. Homely's proposed edge is the *combination* of room-compatible design judgment, distinctive new/used discovery, verified availability, faithful visualization, and collaborative ongoing alternatives. This edge is unproven; source-backed reasoning or visual search alone is not distinctive, and no claim that Homely beats every incumbent is established.

## Next validation gates

Observe real professional sourcing and compare the full decision process with existing tools and native alerts. Test access and evidence freshness by source, exact-variant stock confirmation, delivery cost, and how often useful options survive verification. Prototype and measure actual-product visualization fidelity and fit against known room/product geometry. Validate willingness to pay, adoption, return/referral, acquisition cost, AI/human cost-to-serve, and an affiliate program's allowed incentives before treating scenarios as operating plans.

## Historical precedence

The [original handoff](historical-handoff/ai-furniture-app-codex-handoff/ONE_MASTER_CONTEXT.md) is a preserved historical V0 proposal, including web-first, constrained search, fixed result counts and exclusions. Its `AGENTS.md`, prompts, `CODEX_START_HERE.md`, build plan, decisions and schemas are historical source material, not operative instructions for this repository. Where its V0 requirements conflict with the later vision and firm requirements above, use this current decision record. The [competitor analysis](research/AI-Furniture-App-Competitor-Analysis.md) and [business plan](research/AI-Furniture-App-Business-Plan.md) are dated research snapshots; they may contain proposed sequencing that predates the two firm requirements. Preserve and cite them, but do not silently promote proposals to final product decisions.

## September17 approved room setup update
Use mockups/13-approved-room-flow.png for the current room picker and setup flow: room photo suggestions, explicit keep/start-scratch choice, saved budget, tailored categories, one real green composer. New room is accessible from the project chooser. Generic setup imagery remains labelled inspiration even when an original project photo exists; the original stays in project details/canvas. Retained pieces are explicit notes until actual object selection is implemented.

## Fit-qualified recommendations — firm requirement; next mockup pending approval
Only recommend a product as fitting retained furniture when its applicable measured constraints have been validated. This supersedes any skip-measurements-and-recommend assumption. Missing, conflicting, or insufficient dimensions block fit-qualified results; saving and resuming later must remain available. Optional inspiration browsing is a separate, clearly labelled experience and must never be described as fitting recommendations.

The fit gate requires the user's confirmation of the retained object and exact variant, measured or traceable retained-object dimensions, candidate-specific dimensions for the exact candidate variant, and deterministic geometric constraints with explicit clearance tolerances and supporting evidence. Keep units, measurement/source provenance and unresolved uncertainty visible. Conflicting sources require resolution; do not silently select a favourable value or substitute photo estimates for measurements.

For dining chairs, validate arm clearance beneath the lowest relevant table edge/apron, seat-to-table relation, chair width against table leg spacing, and the requested chair count/arrangement and usable clearance as applicable. Height alone does not establish universal fit. Any fit statement is limited to the measured constraints actually validated; do not promise an absolute guarantee beyond that evidence.

Add this measurement gate before fit-qualified results in the next design/spec, including an explanation of what is missing, source uncertainty handling, and graceful save/resume. The revised flow still awaits final mockup approval. This records a requirement only; no new implementation is authorized before that approval, and existing code must not be represented as already satisfying the expanded gate.

## Approved nine-step flow
User approved mockups/14-approved-nine-step-flow.png and authorized implementation, superseding the prior pending-approval state. Apply all strict fit requirements above. Furnishing choice advances with no new-user default; decide-later keeps retained state unknown. Separate inspiration from fit-qualified products, and saving from explicitly enabled, functioning price monitoring.

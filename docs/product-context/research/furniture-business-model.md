# Business model, customer evidence and route to market

Research date: September 13, 2026. US-first is a planning assumption, not a user-confirmed geographic limit. Professional designers are the initial customer; DIY nonprofessionals are a deliberate later expansion. This memo supports a business plan and product discussion, not authorization to build. All proposed prices, funnels, margins, thresholds and forecasts below are assumptions unless explicitly attributed.

## What the evidence supports—and does not

There is evidence that designers buy specialized software, experiment with AI, and value productivity. It does not establish that furniture sourcing is their biggest pain or that they will buy this proposed assistant. In Houzz's 2025 survey, interior designers' most cited business challenges were finding customers (43%), the economy (28%), and operating costs (23%). Its sample comprised 1,537 residential renovation businesses registered on Houzz, with responses collected in late 2024. These are business-level priorities, not a time-and-motion study; sourcing could still be expensive within delivery work. [Houzz report](https://st.hzcdn.com/static/econ/2025_U.S._Houzz_State_of_the_Industry.pdf).

Houzz's September 1, 2026 AI report says 39% of design firms use AI and 22% of surveyed renovating homeowners used it. Reliability concerns among professionals rose to 37%. It surveyed 601 construction/design businesses and 3,149 renovating homeowners registered on Houzz. These populations are broader than professional interior designers and narrower than all households, respectively. These findings support readiness and a need for trust; they do not prove demand for this specific product. Do not repeat Houzz's monetized productivity estimates as realized customer savings: those convert self-reported time using firm revenue, not marginal labor cost. [Houzz release and methodology](https://www.houzz.com/press/1024/Houzz-Survey-Finds-AI-Adoption-Soars-Among-Construction-and-Design-Pros-While-Homeowners-Rely-on-the-Experts).

The customer problem to test is: repeated searches and verification across stores delay defensible selections, consume unbillable time, and create costly substitutions. This should be measured directly against customer acquisition, client approvals, procurement administration and visual communication, rather than assumed to outrank them.

## Pricing context

| Official offer observed | What it tells us | What it does not tell us |
|---|---|---|
| Mydoma: $58/user/month when paid yearly, plus a stated $450 onboarding investment | A broader professional workflow suite competes for software budget | The number of payers, retention, or willingness to pay $58 for sourcing alone |
| Onton: free search; annual-billing equivalent plans at $8, $20 and $35/month for expanded image/canvas features | Generic discovery faces free alternatives; paid visualization has a low-price reference point | That users will pay similar amounts for verification |
| Havenly: per-room human design, with official pages displaying promotional prices from $99–$159 against $199 regular online pricing | DIY buyers can compare an AI pass with a finite human-assisted project | A stable checkout price or evidence an AI-only offering can charge the same |

Sources: [Mydoma pricing](https://mydomastudio.com/pricing/), [Onton pricing](https://onton.com/pricing), [Onton free search documentation](https://docs.onton.com/), [Havenly services](https://havenly.com/interior-design-services), [Havenly billing help](https://help.havenly.com/en_us/how-does-design-package-pricing-work-S1vuNAyZll). Prices were publicly displayed; no checkout, trial or subscription was completed. Conflicting Havenly promotions warrant a range rather than false precision.

## Recommended entry point: a testable commercial wedge

The updated long-term vision is an intelligent, genuinely easy interior-design companion that transforms how professionals and DIY users research, discover and choose pieces. It should reason across creative sources, including resale/vintage and local marketplaces, and keep looking over time where access permits. It is not limited to a five-card search result, top-retailer APIs, or a quick proof of concept built for market share.

An initial evidence-building use case is independent residential designers and small studios sourcing constrained pieces, including distinctive secondhand finds, under fixed dimensions, budgets and deadlines. The triggering task is a constrained replacement or ongoing hunt: a client-approved style is unavailable, too large, too expensive, or too late, or a distinctive vintage piece has yet to appear. Return alternatives with product evidence, visible unknowns, and a client-ready comparison. Validate whether active vintage/DIY hunters have stronger recurrence than occasional retail shoppers, without silently replacing the professional-first strategy.

This is a hypothesis for a useful entry point, not a proven unoccupied market. Its advantages to test are a concrete urgent job, measurable time savings, and repeated use across clients. A mix of permitted retail and resale access can generate evidence before comprehensive source coverage; the business must not present that staged access as the final vision. Source-access feasibility is itself a central research gate. Designer-provided links should remain usable when processing is permitted even if a merchant pays no commission; user submission does not itself resolve source terms or content rights.

The customer should retain design judgment. Promise faster, better-supported decisions, not guaranteed fit, guaranteed delivery, or autonomous professional design. Delivery confidence requires location, variant, shipping service and fresh seller evidence; a generic in-stock badge is insufficient. Compatibility beyond measured dimensions remains partly judgmental.

## Monetization sequence

1. **Pro paid pilot:** test $49–$99 per sourcing seat/month against a $29–$49 limited project pass. A $79 seat is used below strictly for arithmetic. Price should follow measured time saved and repeat use, not a competitor average. Avoid charging every client collaborator as a professional seat.
2. **Professional subscription after demonstrated recurrence:** bounded sourcing allowance, saved constraints, revision history and exports. Meter expensive work sensibly; unlimited verification is dangerous before measuring cost. Offer annual billing only after customers demonstrate multi-project value.
3. **DIY project pass:** test a $19–$39 finite project allowance (model uses $29). Furniture selection is often episodic, so project completion can be success even when monthly retention falls. Track completed decisions, paid-project repeats and referrals over 6–12 months, not daily usage as the sole success metric.
4. **Affiliate revenue as optional secondary income:** model it separately and set zero in the core solvency case until contracts, eligible merchants and collection rates exist. Disclose compensation and keep ranking independent of commissions. Otherwise a verification proposition loses credibility.

Consumer repeat behavior should not be invented. Wayfair reported 1.88 trailing-year orders per active customer at the end of 2025; this is retailer-specific, includes a broad home catalog, and does not measure AI-tool usage. It is a useful warning against assuming frequent recurring furniture purchases, not proof all DIY customers behave identically. [Wayfair 2025 results](https://www.aboutwayfair.com/category/company-news/wayfair-announces-fourth-quarter-and-full-year-2025-results-reports-further-share-capture-and-strong-profitability).

### Affiliate illustration, not contracted economics

Revenue = attributable qualifying GMV × agreed commission × realized-collection fraction. For 1,000 activated shoppers × 10% purchasing × $500 eligible basket × 3% assumed commission × 70% net realization = **$1,050**, or **$1.05 per activated shopper**. At 1% commission the result is $350; at 5%, $1,750. None of those rates is verified for this company. Returns, canceled orders, merchant coverage, attribution loss and consumer switching affect realization. Furniture GMV is not software revenue or software TAM.

Wayfair's terms confirm affiliate attribution and commission infrastructure but do not establish this startup's rates or access. IKEA Spain advertises up to 5%; that is specifically Spain and must not be imported into a US projection. [Wayfair terms](https://www.wayfair.com/terms?section=wayfair-rewards-program-terms), [IKEA Spain affiliate program](https://www.ikea.com/es/en/campaigns/home-fanatic-recommend-ikea-pub9a336260/).

## Cost-to-serve and viability sensitivity

No product traces or measured costs exist. The following are hypotheses spanning AI, retrieval, refreshes, failed extraction and product checking—not claims about any model provider's price. Define one sourcing run as completing/refining one constrained request; a run can require multiple searches and model calls.

At $79/month and 60 completed runs per seat:

| Assumed variable cost per run | Run costs | Other variable support/payment/hosting assumption | Contribution per seat | Contribution margin |
|---|---:|---:|---:|---:|
| $0.05 | $3 | $8 | $68 | 86% |
| $0.25 | $15 | $8 | $56 | 71% |
| $1.00 | $60 | $8 | $11 | 14% |

These margins exclude salaries, customer acquisition, fixed data licensing, legal costs, taxes and research. Human checking can overwhelm them: 3 minutes/run at an assumed loaded $30/hour is $1.50/run, or another $90/seat/month. A concierge pilot is a learning expense, not evidence of scalable software margins.

At $29 per DIY pass, 20 runs × $0.25 + $3 other variable costs leaves $21 contribution (72%). That cannot sustain arbitrary paid acquisition. Customer acquisition payback should use gross/contribution profit, not headline revenue. At the middle pro case, six-month gross contribution is approximately $336 before churn; this is a candidate CAC ceiling to investigate, not a sourced CAC benchmark. At $20,000 assumed monthly fixed cash costs, $56 contribution requires about 358 paying seats to cover those costs before acquisition spend; at $40,000 it requires 715. This is a sensitivity, not a funding request or a staff plan.

## Bottom-up professional growth model

Illustrative monthly base acquisition funnel: 1,200 qualified professional visitors × 15% trial rate × 50% activation × 20% paid conversion = **18 new paid seats/month**. Qualified visitor means a relevant designer with a real sourcing task, not a social impression. All rates are unvalidated and must be observed separately by channel.

Using constant monthly additions from month one, constant logo/seat churn, $79 monthly price, no expansion, and new additions billed that month:

| Scenario | New paid seats/month | Monthly churn | Month-12 paying seats | Month-12 annualized revenue | First-year recognized subscription revenue |
|---|---:|---:|---:|---:|---:|
| Slow learning | 5 | 6% | 44 | $41,402 | $24,947 |
| Base experiment | 18 | 4% | 174 | $165,218 | $96,164 |
| Strong repeatable acquisition | 60 | 2.5% | 629 | $596,106 | $337,855 |

Formula: seats at month m = additions × [1 − (1 − churn)^m] / churn. Displayed seats rounded; revenue calculations use unrounded expected seats. These scenarios are acquisition capacity examples, not market-share forecasts or an independently calculated SOM. Ramping acquisition later would reduce year-one revenue. Annualized end-of-year revenue is not cash collected and not first-year revenue.

## What “viral” would actually mean

Separate impressions, visitors, active project users, purchases and future repeat customers. One illustrative consumer campaign or burst:

| Scenario | Social impressions | Visit rate | Visitors | Activated project rate | Activated projects | Paid-pass conversion | $29 passes sold | Gross pass revenue |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Small burst | 100,000 | 1% | 1,000 | 20% | 200 | 5% | 10 | $290 |
| Strong burst | 1,000,000 | 2% | 20,000 | 30% | 6,000 | 8% | 480 | $13,920 |
| Breakout stress test | 10,000,000 | 3% | 300,000 | 40% | 120,000 | 10% | 12,000 | $348,000 |

These are conditional scenarios, not probability-weighted predictions. None of the impressions, conversion rates or paid demand has been observed. Repeat visits, duplicate viewers and attribution overlap could reduce unique counts. A hypothetical 20% second-project purchase rate would mean 96 repeat purchasers in the strong-burst case; that rate is not evidence. Consumer pass revenue is transactional and must not be labeled ARR.

Free usage can destroy burst economics: if each activated nonpayer uses $1 of service, the strong burst costs roughly $5,520 just for 5,520 nonpayers; ten-dollar free usage costs $55,200. Put bounded allowances and cached inexpensive discovery before intensive checks.

Viral loop coefficient = sharing fraction × unique qualified recipients per sharer × recipient activation rate. At 25% × 3 × 20%, K = 0.15, far below a self-sustaining K above 1. Sharing client boards is useful distribution, but most client viewers are not additional professional buyers. Count DIY and pro downstream conversion separately. Short-lived social virality does not replace a repeatable acquisition channel.

## Go-to-market experiments

**First professional customers:** recruit through existing professional relationships, local design communities and explicit opt-in research; observe live sourcing tasks and offer a paid concierge experiment after consent. No outreach has been performed. Lead with replacement jobs and documented saved verification time. Designers' existing workflow suites are potential export destinations before they are platforms to replace.

**Repeatable professional channels:** evidence-rich demonstrations on actual briefs, educator/community partnerships, professional referrals, and searchable comparison content for high-intent constraints. Treat each as a hypothesis with CAC measured including founder time, incentives and partner fees. Avoid generic “AI room makeover” traffic as the main professional funnel because it may attract inspiration-only consumers.

**Consumer expansion:** designers' client-facing comparisons, helpful saved shopping lists, creators showing purchase decisions and tradeoffs, and high-intent move/room-refresh queries. Establish separate cohorts because client referrals and broad social audiences have different purchase intent. Expand only after the constrained sourcing engine works and consumer pass economics survive free demand.

## Decision gates before building broadly

All thresholds are proposed learning rules, not industry standards or statistically proven cutoffs.

1. **Problem gate:** 15–20 professional interviews plus observation of at least 30 real sourcing tasks across project types. Record baseline minutes, tools, costly mistakes, frequency, and whether time is billable. Continue with the sourcing wedge if at least 10 designers identify repeated consequential tasks and at least 5 commit money to a trial; otherwise narrow the segment or reconsider the problem.
2. **Utility gate:** at least 50 matched briefs against each participant's current method and leading competitor. Blind-rate acceptable products, hard-constraint failures, unknowns, evidence accuracy, elapsed designer time and preference. Target median time reduction of 50% with no increase in false hard-constraint claims. Unknown fields must not count as verified passes.
3. **Commercial gate:** run a 6–8 week paid pilot with approximately 10–15 designers. Seek at least 60% using it on a second real brief and 50% electing to continue paying at the tested price. With a tiny sample these are directional signals; inspect who did not return and why, rather than treating them as precise population estimates.
4. **Data/operations gate:** measure coverage on the actual target merchant set; verify permission/access feasibility, variant resolution, location-sensitive delivery, refresh cost and extraction failure. Stop promising verification where evidence is inaccessible. Measure distribution of cost per run and manual intervention, not only average API cost.
5. **Economics gate:** demonstrate at least 70% contribution margin at target use, investigate acquisition payback under six months for pro cohorts, and require positive per-project consumer contribution including free-use burden. If human checking remains necessary, charge for it explicitly or narrow scope.

Next product conversation should decide which observed task has urgency, measurable advantage and repeat use while advancing the broader transformation vision. Pro-first and DIY-later can share an intelligent research foundation while requiring different onboarding, packaging, distribution and retention definitions. A unique entry point is earned through customer evidence and a benchmark, not declared from feature comparison. Validation stages are staged investment in that vision, not a mandate to launch a minimal product quickly.

## Persistent research and resale: updated economics and feasibility

This extension changes both customer value and cost. A saved hunt can notice a rare local listing when it appears, remember why previous suggestions failed, and adapt the search. The value is ongoing attention plus judgment. However, a one-off listing can disappear before notification, attributes may be missing, and condition, seller trust, pickup radius, transport cost, restoration and return limitations all matter. A low sticker price is not an all-in bargain. Seller statements and image-based inferences must not be described as independently verified condition or authenticity.

**Source access is differentiated:** eBay documents a Browse API for keyword and image search and item detail/refresh, but production eligibility, additional licensing and quotas still apply. Its default Browse limit is 5,000 calls/day for most methods; higher capacity requires a growth check. The vehicle compatibility endpoint does not validate furniture compatibility. Craigslist's terms restrict interoperating services and collection absent separate permission. Facebook's help page distinguishes authorized from unauthorized scraping and describes enforcement; this research has not established a general approved Marketplace discovery integration. Therefore do not commit to automatic comprehensive monitoring of Facebook Marketplace or Craigslist. Source partnerships, specifically approved access, permitted user-directed assistance, and source-native saved-search handoffs need investigation; none is a license to bypass restrictions. [eBay Browse guide](https://www.developer.ebay.com/api-docs/buy/static/api-browse.html), [eBay limits](https://www.developer.ebay.com/develop/get-started/api-call-limits), [Craigslist terms](https://www.craigslist.org/about/terms), [Facebook scraping guidance](https://www.facebook.com/help/463983701520800).

### Active-hunt-day sensitivity

Define one active-hunt-day as one saved brief monitored for one day, regardless of whether the user opens the app. Cost = source checks/day × assumed cost/check + deeper candidate analyses/day × assumed cost/analysis. A check can involve several billable operations. Rates below include placeholder retrieval/AI expenses and are not source/API fee quotes.

| Illustrative intensity | Source checks/day | Cost/check | Deep analyses/day | Cost/analysis | Cost/active-hunt-day | 30-day cost for one hunt |
|---|---:|---:|---:|---:|---:|---:|
| Light | 5 | $0.01 | 1 | $0.05 | $0.10 | $3.00 |
| Moderate | 20 | $0.02 | 2 | $0.10 | $0.60 | $18.00 |
| Intensive | 100 | $0.02 | 5 | $0.20 | $3.00 | $90.00 |

At three simultaneous hunts, monthly monitoring alone becomes $9, $54 or $270, before interactive sourcing, support, payment costs and fixed infrastructure. A $79 professional subscription can support the light case; the moderate case severely compresses the earlier $56 contribution, and the intensive case is loss-making. Do not add monitoring costs to a run estimate that already includes those same operations; maintain separate interactive and monitoring cost ledgers.

For a $29 consumer 30-day pass with one hunt, monitoring leaves $26, $11 or negative $61 before any other costs. Thus a single unlimited saved-hunt price is not sustainable by assumption. Candidate experiments: a project pass with a clear duration and bounded active hunts; professional subscriptions including a measured hunt-day allowance; optional higher-frequency research where supported. These are pricing hypotheses, not a final user interface.

Expire or pause hunts when purchased, project-completed, stale or at an explicitly communicated limit. Ask whether the user still wants an unresolved search rather than running indefinitely. Use source-native notifications or licensed change feeds where available, deduplicate work across overlapping hunts where permitted, and reserve expensive reasoning for new or changed candidates. Notification usefulness matters more than raw scan count. At 1,000 concurrent hunts and five eBay calls per hunt/day, a hypothetical deployment already uses 5,000 calls/day before detail fetches; scaling requires batching, permitted feeds and approved limits, not merely more compute.

Paid subscription/project value becomes more important in resale because private listings may generate no affiliate revenue. Use zero affiliate income in the saved-hunt base model. Ranking by commissions would also systematically suppress creative nonaffiliate sources central to the vision.

Add measurement gates: time from listing appearance to useful alert; accepted candidate rate; false/duplicate notification rate; cost per useful discovery; share of target sources with approved sustainable access; and real outcome after pickup/transport. Interview vintage-focused designers and DIY hunters separately to test whether alert urgency changes willingness to pay. No monitor, account, outreach or source integration has been created during this research.

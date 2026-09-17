# AI furniture sourcing app: US market sizing memo

Research date: September 13, 2026. Working geography: United States; geography is a planning assumption pending founder confirmation. Professional interior designers first; consumer DIY expansion later. This is a transparent opportunity model, not a forecast or demonstrated willingness to pay.

## What the evidence supports

The professional beachhead is a market of **tens of thousands of potential users**, not millions. The consumer expansion could reach millions of households, but usage is episodic. Model professional recurring seats separately from annual consumer project purchases. Furniture spending and software revenue are different markets.

### Source ledger and counting rules

| Input | Verified evidence | Appropriate use |
|---|---|---|
| US interior-designer occupation | BLS currently reports **97,100 jobs in 2025**, including **26% self-employed**; specialized design services account for 30%, architectural/engineering services 14%, retail trade 12%. Page updated August 27, 2026. | Occupational base for professional seat opportunity, not firm count; jobs are an approximation to unique potential seats. [BLS Occupational Outlook Handbook](https://www.bls.gov/ooh/arts-and-design/interior-designers.htm) |
| Payroll employment versus all employment | OEWS excludes self-employed workers and owners/partners in unincorporated firms. | Never add self-employed estimates to the already-inclusive OOH total. [BLS OEWS concepts](https://www.bls.gov/opub/hom/oews/concepts.htm) |
| Alternate industry estimate | ASID's October 2025 release cites 69,580 employed designers and a separate Barnes estimate of 56,449 self-employed, and projects nearly 17,500 design firms. | An industry cross-check, not a Census count and not directly comparable with the newer BLS series. Do not average these estimates, add firms to people, or treat their sum as a precise TAM. [ASID 2025 release](https://www.asid.org/news/asid-releases-2025-state-of-interior-design-report) |
| US households | **132,737,146 households**, 2024 ACS one-year estimates. | Broad household ceiling. Not annual furniture purchasers, individual consumers, registered accounts, or paid subscribers. [Census US profile results](https://data.census.gov/all?g=010XX00US%2C%240400000&q=United+States&y=2024) |
| Mobility | **11.8% of people** moved residence in the prior year in 2024. | Evidence for recurring life-event demand; cannot multiply this person-level rate by households to produce a verified moving-household count. [Census mobility summary](https://www.census.gov/topics/population/migration/guidance/acs-1yr.html) |
| Renovation incidence | JCHS tabulations report approximately **25.8m homeowners making improvements** in 2023, 29.7% of owners. | Context only: includes replacement/maintenance-related improvements; not a count of room-furnishing customers. AHS-based reporting conventions matter. Do not add these households to movers because populations overlap. [Harvard JCHS report, Figure 7](https://www.jchs.harvard.edu/sites/default/files/reports/files/Harvard_JCHS_Improving_Americas_Housing_2025.pdf) |

**Household vintage note:** the ACS 2024 one-year count differs from the 2020–2024 five-year QuickFacts count of 129.2m; do not combine or average these differently timed estimates. This model consistently uses the 2024 one-year count.

**Vintage warning:** search engines still surface the previous BLS edition with 87,100 jobs and 21% self-employed for 2024. Use the current 2025 edition consistently. The change between editions is not itself proof of a comparable one-year growth rate.

**Business-count limitation:** an establishment is a location; a firm may own several locations. Census CBP excludes nonemployer businesses. Nonemployer businesses also are not synonymous with self-employed individuals. NAICS 541410 captures interior-design-service businesses, while interior designers also work in other industries. The current detailed Census numeric table could not be retrieved in this research pass, so no unverified firm count is inserted. This does not prevent a seat-based model. [Census CBP glossary](https://www.census.gov/programs-surveys/cbp/about/glossary.html), [Census nonemployer FAQ](https://www.census.gov/programs-surveys/nonemployer-statistics/about/faq.html).

## Professional TAM and SAM

Pricing below is an **assumption to test**, not a market-established price. Use $49 per paid seat per month ($588/year), with sensitivity at $29 and $79. Annual prices are undiscounted equivalents before fees, tax, refunds, and churn.

**Broad US professional TAM:** 97,100 occupational seats × $588/year = **$57.1m annual software revenue capacity** at hypothetical universal adoption. Price sensitivity: $33.8m at $29/month to $92.1m at $79/month. Universal adoption is not expected. Designers whose employers restrict purchasing, non-furniture specializations, and infrequent sourcing reduce the practical market.

**Beachhead candidate pool:** self-employed plus designers in specialized design services is approximately 56% of the occupation, or 54,400 seats. This is a segment-selection proxy; it does not establish residential specialization, firm size, frequent sourcing, or willingness to pay.

**Initial SAM hypothesis:** suppose 40–70% of that candidate pool has recurring furniture-sourcing work, uses covered suppliers, and can adopt an independent tool. Then serviceable seats are **21,800–38,100**, or **$12.8m–$22.4m annual capacity** at $49/month. Use **30,000 seats / $17.64m** as a rounded middle planning case. These coverage factors are unmeasured assumptions requiring customer research and a supplier-coverage audit. SAM is not sales pipeline.

Implication: a strong niche SaaS business may be possible from US professionals alone. A very large outcome requires consumer commerce, expansion into additional professional roles/geographies, substantially higher organizational value, or a combination. Those adjacencies should be sized separately after evidence exists.

## Three-year professional SOM: operational scenarios

These are targets conditional on distribution, product performance and retention—not probabilities or industry benchmarks. Qualified trials mean unique relevant designers, not website visits. The retention factor simplifies cohorts and should later be replaced with monthly cohort accounting.

Formula: cumulative unique qualified trials by year 3 × activation × paid conversion among activated users × share still paid at year 3 = ending paid seats.

| Scenario | Qualified trials | Activation | Paid conversion | Still paid factor | Ending paid seats | Ending ARR at $49/month | Share of 30,000-seat middle SAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| Conservative | 4,000 | 30% | 30% | 70% | 252 | $148,176 | 0.84% |
| Working target | 12,000 | 40% | 30% | 70% | 1,008 | $592,704 | 3.36% |
| Strong execution | 25,000 | 50% | 35% | 70% | about 3,063 | about $1.80m | about 10.2% |

The upper case is demanding: it requires exposing a large part of a narrow market to a qualified trial and sustaining retention. The trial totals average roughly 111, 333, and 694 new qualified trials per month over 36 months, respectively. Actual ramp would start smaller and need substantially greater later acquisition. Distribution could combine direct recruitment, associations, educators, studios and designer-to-designer sharing, but no partnership is assumed secured.

ARR is an ending run rate, **not** total year-three recognized revenue and not cumulative three-year revenue. Multi-seat studios require explicit account-to-seat conversion. Gross margin must subtract data licensing, model/search costs and support; human verification can change economics materially.

## DIY TAM, SAM and consumer monetization

**Broad audience ceiling:** 132.7m US households. Do not present all of them as current buyers.

**Annual active-project TAM hypothesis:** assume 10–20% of households annually undertake a furnishing/decorating decision substantial enough to seek assistance. That produces **13.3m–26.5m household-project buyers**. This rate is not measured by the Census mover or Harvard improvement statistics; those establish adjacent demand, not the assumed furnishing incidence. One household is counted once per year in this version, even if it undertakes several projects.

At a hypothetical **$29 project pass**, theoretical annual project-fee TAM is **$385m–$770m**, conditional on universal purchase by that assumed active population. At a $39 pass, the same assumed activity produces $518m–$1.04bn theoretical capacity. These are sensitivity ranges, not evidence that these people would pay. Free retailer tools and general AI substitutes may sharply reduce paid demand.

**DIY SAM hypothesis:** apply a 25–50% serviceability factor to that annual active-project population for supported retailers, geography, project type, sufficient budget, and online workflow fit. This yields **3.3m–13.3m serviceable household projects per year**, equivalent to **$96m–$385m** at universal $29 purchase. Midpoint working model: 132.737m × 15% incidence × 40% serviceability = **7.96m projects / $231.0m annual capacity**. Willingness to pay and obtainable adoption are still excluded from this SAM.

**A one-million-user viral event is not a million customers.** Define the metric and period. The table models unique new account registrations in one launch/viral year, qualified project activation within that year, and one paid pass per paying account. It is not a prediction of virality, retention, or three-year cumulative users. Deduplicate household members for household-market-share comparisons.

| Illustrative reach | New accounts during year | Qualified project activation | Paid share of activated | Paid project customers | Gross project-fee revenue at $29 |
|---|---:|---:|---:|---:|---:|
| Smaller consumer release | 100,000 | 20% | 3% | 600 | $17,400 |
| Significant viral reach | 1,000,000 | 25% | 5% | 12,500 | $362,500 |
| Exceptional reach stress case | 5,000,000 | 30% | 8% | 120,000 | $3,480,000 |

All funnel rates are assumptions. Even the middle scenario needs distribution evidence; the exceptional case belongs in a stress test, not a base business plan. These are annual transactions, **not ARR**. No part of the consumer scenario should be added to professional ARR and labeled recurring revenue.

Affiliate revenue may be modeled separately: completed attributable merchandise spend × eligible merchant coverage × contracted commission rate × (1 − returns/cancellations). Do not multiply total US furniture spending by a commission rate. Example only: $10m completed attributable eligible GMV × 3% net commission = $300,000 revenue, before operating expenses. The commission and attribution are unproven; do not book them before agreements exist. The same furniture purchase should not be counted twice in professional and consumer GMV. Paid recommendations also create an incentive-design question if the product promises impartial sourcing.

## What would make the model defensible enough to fund a build?

1. Interview 15–20 designers across solo, small studio, residential and mixed practices; measure actual monthly sourcing frequency, decision-maker, spend authority and suppliers. Then recruit a small paid concierge pilot. These are recommended sample sizes, not completed research.
2. Use real briefs to quantify time saved, hard-constraint accuracy, shortlist acceptance and supplier coverage. Track reasons the tool cannot serve a project. Convert those observations into the SAM serviceability factor.
3. Test at least three prices with real payment commitments, distinguishing individual seats from studio accounts; record cancellation reasons and 30/60/90-day repeat use.
4. Test consumer project-pass versus free/affiliate approaches independently. A consumer signup only becomes meaningful when it produces a real shortlist, saved project, or purchase-linked outcome.
5. Measure invitation rate × invitation acceptance × project activation for any proposed viral loop; no credible forecast of virality exists before these inputs. Professional client-sharing can expose consumers to the tool, but a client viewing a paid designer's shortlist is not automatically a DIY customer.
6. Obtain a consistent latest-vintage Census employer/nonemployer business table if the commercial model switches from seats to firm subscriptions. Do not use the current industry-association firm projection as a verified Census denominator.

## International expansion

Not included in these totals. A defensible country model requires compatible designer occupation definitions, household counts, local retailer coverage, delivery reliability and pricing. Multiplying US opportunity by global population would be misleading. Canada, UK and other markets may be attractive hypotheses, but this memo makes no unsupported global TAM claim.

## Updated scope: persistent secondhand and local sourcing

The founder's expanded concept includes persistent research across Facebook Marketplace, Craigslist, eBay and other local/secondhand sources, alongside retail. This may make budget-constrained furnishing, matching existing pieces, vintage discovery and time-bounded saved searches better consumer entry hypotheses. It does not by itself enlarge the verified population base: secondhand shoppers overlap with the household population already modeled, and many designers also source vintage. Do not add resale shoppers or resale merchandise spending to the software TAM.

In the SAM formula, replace generic supplier coverage with the proportion of real briefs for which the agent can reliably access useful sources and support local radius, pickup/delivery and seller responsiveness. Persistent hunts could justify monthly rather than project pricing if users keep searches running; that is a testable behavior, not recurring revenue established by the concept. Human follow-up, listing disappearance, duplicate listings and frequent revisits can increase variable costs. A viral bargain discovery may attract many browsing users with low paid conversion, so retain distinct registered, activated, paid and retained metrics. Geographic density and successful matches per search are more meaningful early indicators than total catalog size.

# AI Furniture App — Codex Development Handoff

**Status:** V0 development kickoff  
**Primary hypothesis:** An AI sourcing agent can give an interior designer five more useful product recommendations than their normal Google/Pinterest sourcing process because it understands the complete purchasing context at the same time.

---

## 1. Product in one sentence

An AI sourcing agent for interior designers that searches for furniture and decor, understands the full purchasing context, filters out bad fits, and returns five purchase-ready recommendations with evidence explaining why each item works.

The product is **not** just "AI that finds furniture." The advantage is:

> The AI understands why a particular item will or will not work for a particular project.

---

## 2. The V0 hypothesis

### Question to prove

Can the product give an interior designer **five genuinely useful product recommendations** that are better than what the designer would find through their normal Google/Pinterest workflow because the system can reason over all constraints at once?

### What "better" means

A recommendation is better when it is not only visually relevant, but also materially more purchase-ready because it accounts for:

- item type
- reference image / visual direction
- natural-language intent
- budget
- dimensions
- location
- delivery deadline
- required style
- required material or features
- explicit dislikes / disqualifiers

The V0 should optimize for **usefulness**, not number of results.

---

## 3. V0 user

### Primary user

Professional interior designers who regularly source furniture, lighting, and decor for client projects.

### Initial behavior being replaced

The user currently:

1. searches Google
2. searches Google Shopping
3. searches individual retailer websites
4. uses Pinterest or Instagram for visual discovery
5. opens many tabs
6. manually checks dimensions
7. manually checks prices
8. manually checks materials
9. manually checks shipping / availability
10. tries to remember project-specific dislikes and requirements

The V0 compresses that workflow into one sourcing request and one ranked shortlist.

### Do not broaden V0 yet

Do not optimize for:

- general consumers
- furniture retailers
- architects
- procurement teams
- contractors
- marketplace sellers

Those can be future segments.

---

## 4. Exact V0 problem

Interior designers can find visually similar furniture online, but existing search workflows do a poor job combining all project constraints simultaneously.

The designer loses time because a visually attractive result may later fail because:

- it is too large
- the seat height is wrong
- the price is over budget
- it will not arrive in time
- the finish conflicts with an existing item
- the material is excluded
- it is too bulky
- the retailer does not ship to the project location
- it is out of stock
- a required feature is missing

The V0 should surface these failures before the designer spends time evaluating the item.

---

## 5. Core promise

> Tell the app what you need, show it the visual direction, give it the purchasing constraints, and receive five strong options that are actually viable for the project.

The result should feel closer to a good junior sourcing assistant than a search engine.

---

## 6. Required user inputs

The canonical sourcing form contains nine inputs:

1. **Item needed**
2. **Reference image**
3. **What I want**
4. **Budget**
5. **Dimensions**
6. **Location**
7. **Delivery deadline**
8. **Must-have style / material / features**
9. **What would make the result bad**

### Input philosophy

The system should accept natural language. It should not force the designer to translate their thinking into rigid filters.

Structured fields exist to improve reliability, but the interface should remain fast.

### Example

- Item: Dining chairs
- Reference image: uploaded
- What I want: Warm Scandinavian chairs with a slightly vintage feel that work with a dark walnut dining table
- Budget: Max $350 per chair
- Dimensions: Must fit six comfortably around existing table
- Location: Los Angeles
- Delivery deadline: [date]
- Must-have: Warm wood, visually light, comfortable enough for long dinners
- Bad result: Bouclé, black metal legs, very bulky silhouette

---

## 7. Existing-item compatibility variation

The app also needs a sourcing mode built around something the designer already owns.

Required inputs:

1. **Existing item**
2. **What I need**
3. **Style**
4. **Budget**
5. **Dimensions**
6. **Location**
7. **Things I do NOT want**

Example:

- Existing item: Dark walnut dining table
- What I need: 6 dining chairs
- Style: Scandinavian, warm, slightly vintage
- Budget: Maximum $350 per chair
- Dimensions: Must fit comfortably around the table
- Location: Los Angeles
- Things I do NOT want: Bouclé, black metal legs, very bulky chairs

This should use the existing item as a compatibility anchor, not merely another keyword.

---

## 8. What the AI must do

For every sourcing request, the system should:

1. parse the request into structured constraints
2. distinguish hard constraints from preferences
3. infer useful search language and synonyms
4. retrieve a broad candidate set
5. normalize candidate data
6. verify important purchase facts where possible
7. eliminate hard-constraint failures
8. score remaining candidates
9. diversify the shortlist so all five are not near-duplicates
10. return exactly five strong recommendations when five defensible options exist
11. explain why each recommendation fits
12. explicitly disclose uncertainty
13. never present unknown price, dimensions, stock, shipping, or delivery as confirmed
14. capture evidence links and timestamps for time-sensitive claims
15. learn from explicit user feedback during the session

---

## 9. Hard constraints vs soft preferences

### Hard constraints

Hard constraints should normally disqualify a candidate.

Examples:

- maximum budget
- maximum width
- minimum seat height
- excluded material
- excluded color
- must ship to location
- must arrive by deadline
- quantity availability when known
- required item type
- required mounting type
- required outdoor rating

### Soft preferences

Soft preferences affect ranking but should not automatically disqualify.

Examples:

- Scandinavian
- warmer wood tone
- slightly vintage
- visually light
- curved back
- feels special
- not too trendy
- resembles reference image
- works with existing item

### Ambiguity rule

When user language is ambiguous, prefer preserving a candidate with a lower confidence score rather than pretending a hard fact is known.

---

## 10. Search / recommendation pipeline

```text
User request
    ↓
Constraint extraction
    ↓
Hard vs soft classification
    ↓
Search-query generation
    ↓
Candidate retrieval
    ↓
Product normalization
    ↓
Evidence verification
    ↓
Hard-constraint filtering
    ↓
Compatibility + preference scoring
    ↓
Diversity pass
    ↓
Top 5
    ↓
Human-readable reasons + warnings + source links
```

### Candidate count

Do not search for only five products.

Recommended V0 flow:

- retrieve ~30–100 raw candidates
- normalize and deduplicate
- verify the strongest ~15–30
- rank
- return five

Exact counts can adapt to search-provider cost and latency.

---

## 11. Result card requirements

Each of the five results should contain:

- product name
- retailer / source
- primary image
- current observed price
- price basis: per item / set / trade price if known
- dimensions
- key material / finish
- availability status if known
- shipping / delivery information if known
- source URL
- timestamp for time-sensitive observations
- "why it fits"
- "what to watch"
- compatibility score or fit label
- confidence state

### Good explanation

"Strong fit because the warm oak tone complements the walnut table without matching it exactly, the open-back silhouette keeps the dining area visually light, and the observed price is under your $350/chair cap."

### Bad explanation

"This chair matches your style and would look great."

The explanation must connect the product back to concrete constraints.

---

## 12. Evidence and uncertainty rules

The product lives or dies on trust.

### Never silently invent

Never invent:

- price
- dimensions
- stock
- shipping
- delivery date
- material
- finish
- retailer policies

### Field-level state

Important fields should support:

- `confirmed`
- `observed`
- `inferred`
- `unknown`
- `conflicting`

### Evidence

Where possible, attach:

- source URL
- source type
- observed value
- observed timestamp

### Delivery

Delivery should be treated as time-sensitive and location-sensitive.

If delivery cannot be verified, say so.

"Likely ships in 2–3 weeks" is not equivalent to "arrives by October 5."

---

## 13. Ranking model

V0 does not need a trained recommender.

Use transparent scoring.

### Gate first

Candidates that clearly violate hard constraints should be removed.

### Example score

```text
fit_score =
  0.30 * visual_style_fit +
  0.20 * functional_fit +
  0.15 * existing_item_compatibility +
  0.15 * budget_fit +
  0.10 * dimension_fit +
  0.05 * delivery_confidence +
  0.05 * source_quality
```

Weights should be configurable.

### Penalties

Apply penalties for:

- missing critical facts
- weak source quality
- ambiguous product identity
- duplicate / near-duplicate results
- likely marketplace knockoffs
- price uncertainty
- unclear shipping

### Diversity

Five results should represent a useful range while remaining on-brief.

Avoid five color variants of the same chair.

---

## 14. V0 user actions after results

Keep this narrow.

The user should be able to:

- open product page
- save a result
- reject a result
- provide a rejection reason
- ask for replacements
- refine the request in natural language

Useful rejection reasons:

- too expensive
- wrong style
- wrong material
- too large
- too small
- too bulky
- delivery too slow
- feels cheap
- too generic
- does not work with existing item
- other

Do not build a large project-management workflow yet.

---

## 15. V0 must include

1. responsive sourcing form
2. reference-image upload
3. natural-language request
4. structured core constraints
5. actual web/product retrieval
6. candidate normalization
7. hard-constraint filtering
8. ranked five-result shortlist
9. source URLs
10. evidence / uncertainty handling
11. product images
12. save
13. reject + reason
14. replacement request
15. basic request history
16. instrumentation for V0 evaluation

---

## 16. Deliberately excluded from V0

Do not build unless needed to prove the core hypothesis:

- native iOS app
- native Android app
- full procurement
- checkout
- payments
- trade-account login automation
- purchase orders
- invoicing
- client presentation builder
- room rendering
- AR placement
- 3D models
- real-time camera call with the AI
- voice call with persistent live video
- social feed
- marketplace
- retailer portal
- collaborative multi-user project management
- automatic ordering
- returns management
- full CAD integration

These may be valuable later. They are not required to test the V0 hypothesis.

---

## 17. Platform recommendation for V0

Build a **responsive web app, desktop-first**.

Why:

- professional sourcing is tab-heavy and comparison-heavy
- designers often work from computers
- web app reduces platform-development overhead
- image upload still works on mobile
- the same product can later be wrapped or extended into native apps
- voice and camera workflows can be explored later without making them V0 dependencies

Mobile should be usable, but V0 does not need to be mobile-first.

---

## 18. Voice and camera — future direction, not V0

Voice can eventually reduce data-entry friction.

Potential workflows:

- "I need six chairs for this table, under $350 each, warm wood, no bouclé."
- conversational refinement of results
- hands-free sourcing while walking through a room
- capture room constraints verbally

Camera can eventually add live physical context:

- point at an existing table
- point at a wall or empty corner
- show finish / color / material
- discuss what should be sourced around it

A combined live camera + voice experience is feasible as a future product direction, but it should not block V0.

For now:

- allow image upload
- preserve the data model so an image can be associated with an existing item or room
- keep modality-specific code behind interfaces

---

## 19. Recommended technical architecture

### Front end

- Next.js
- TypeScript
- React
- Tailwind CSS or equivalent utility styling
- responsive desktop-first layout

### Backend

For V0, use the application server/API layer inside the web app unless scale requires separation.

Responsibilities:

- auth
- sourcing request persistence
- image upload orchestration
- AI calls
- search provider calls
- candidate normalization
- scoring
- result persistence
- feedback

### Database

PostgreSQL.

Supabase is a reasonable V0 choice because it can provide:

- Postgres
- authentication
- storage
- row-level security
- fast setup

Keep database access behind a small repository/service layer so provider choice can change.

### Storage

Store:

- uploaded reference images
- optional cached product thumbnails where legally appropriate
- derived image embeddings only if required later

Prefer hotlinking or using authorized product image URLs for V0 if licensing and retailer terms allow.

### AI

Use an LLM for:

- constraint extraction
- query expansion
- candidate interpretation
- compatibility reasoning
- explanation generation

Do not ask the model to invent live product facts.

### Search

Implement a `SearchProvider` abstraction.

```ts
interface SearchProvider {
  search(query: SearchQuery): Promise<RawSearchResult[]>
}
```

Do not couple the product to one search provider.

Potential provider types:

- web search API
- shopping search API
- retailer APIs
- affiliate feeds
- structured product feeds

### Verification

Create a separate verification layer.

```ts
interface ProductVerifier {
  verify(candidate: ProductCandidate, context: RequestContext): Promise<VerifiedProduct>
}
```

This is important because discovery and factual verification are different jobs.

---

## 20. Suggested code architecture

```text
app/
  (auth)/
  sourcing/
  requests/
  api/

components/
  sourcing/
  results/
  feedback/
  shared/

lib/
  ai/
  search/
  products/
  ranking/
  verification/
  db/
  analytics/
  schemas/

docs/
prompts/
examples/
```

### Separation rules

Keep these concepts separate:

- user input
- normalized constraints
- raw search result
- normalized product candidate
- verified product
- ranked recommendation
- user feedback

Do not collapse them into one giant object.

---

## 21. Core domain model

### User

```ts
type User = {
  id: string
  email: string
  name?: string
}
```

### SourcingRequest

```ts
type SourcingRequest = {
  id: string
  userId: string
  mode: "direct" | "existing_item"
  itemNeeded: string
  whatIWant?: string
  budget?: BudgetConstraint
  dimensions?: DimensionConstraint[]
  location?: LocationConstraint
  deliveryDeadline?: string
  mustHaves: string[]
  dislikes: string[]
  existingItem?: ExistingItem
  referenceImageUrls: string[]
  status: "draft" | "searching" | "complete" | "failed"
  createdAt: string
}
```

### NormalizedConstraint

```ts
type Constraint = {
  id: string
  type:
    | "item_type"
    | "budget"
    | "dimension"
    | "location"
    | "delivery"
    | "style"
    | "material"
    | "feature"
    | "exclusion"
    | "compatibility"
  value: unknown
  hardness: "hard" | "soft"
  confidence: number
  sourceText?: string
}
```

### ProductCandidate

```ts
type ProductCandidate = {
  canonicalUrl: string
  title: string
  retailer?: string
  imageUrl?: string
  rawPriceText?: string
  rawDimensionsText?: string
  rawMaterialText?: string
  sourceSnippet?: string
  sourceType: string
}
```

### VerifiedProduct

```ts
type VerifiedField<T> = {
  value?: T
  state: "confirmed" | "observed" | "inferred" | "unknown" | "conflicting"
  evidenceUrl?: string
  observedAt?: string
  notes?: string
}

type VerifiedProduct = {
  candidate: ProductCandidate
  price: VerifiedField<Money>
  dimensions: VerifiedField<ProductDimensions>
  materials: VerifiedField<string[]>
  availability: VerifiedField<string>
  delivery: VerifiedField<DeliveryEstimate>
}
```

### Recommendation

```ts
type Recommendation = {
  productId: string
  fitScore: number
  scoreBreakdown: Record<string, number>
  reasons: string[]
  warnings: string[]
  hardConstraintPass: boolean
  confidence: number
  rank: number
}
```

### Feedback

```ts
type RecommendationFeedback = {
  requestId: string
  productId: string
  action: "saved" | "rejected" | "opened" | "replacement_requested"
  reason?: string
  freeText?: string
  createdAt: string
}
```

---

## 22. AI output contracts

Use structured output wherever possible.

### Constraint extraction output

```json
{
  "item_type": "dining chair",
  "quantity": 6,
  "hard_constraints": [
    {
      "type": "budget_max",
      "value": 350,
      "unit": "USD",
      "basis": "per_item"
    }
  ],
  "soft_preferences": [
    "Scandinavian",
    "warm",
    "slightly vintage",
    "visually light"
  ],
  "exclusions": [
    "boucle",
    "black metal legs",
    "very bulky"
  ],
  "open_questions": []
}
```

### Recommendation reasoning output

Reason over verified candidate facts only.

The model should receive:

- normalized request
- reference-image analysis if available
- verified product data
- missing-data indicators
- scoring inputs

The model should not be used as the source of truth for live commerce facts.

---

## 23. Reference-image handling

For V0, reference-image analysis should extract design signals such as:

- item category
- silhouette
- visual weight
- dominant materials
- dominant finish / color family
- leg style
- back shape
- upholstery presence
- texture
- era cues
- style labels
- notable details

Do not reduce the image to one style label.

Example output:

```json
{
  "silhouette": ["slim", "open-back", "softly curved"],
  "materials": ["wood", "woven seat"],
  "color_family": ["warm medium wood", "natural"],
  "style_signals": ["Scandinavian", "mid-century-adjacent", "vintage"],
  "avoid_overmatching": true
}
```

---

## 24. Existing-item compatibility logic

"Matches" should not mean "same color."

Compatibility can consider:

- wood-tone relationship
- material contrast
- silhouette balance
- visual weight
- period / style relationship
- repetition vs contrast
- scale
- finish undertone
- room hierarchy

Example:

A dark walnut table may work better with a lighter warm-oak chair than with an exact dark-walnut match if the user wants a lighter Scandinavian result.

The explanation should articulate that reasoning.

---

## 25. Search query generation

Do not use a single literal query.

Generate multiple query families.

Example for the dining-chair request:

- warm oak Scandinavian dining chair curved back
- vintage Scandinavian wood dining chair natural seat
- slim wood dining chair no metal warm oak
- Danish style dining chair under 350
- spindle/open-back oak dining chair warm modern
- dining chair walnut table light wood contrast

The query generator should incorporate exclusions carefully.

Searching `"no boucle"` is sometimes useful; often it is better to search positive attributes then filter bouclé out later.

---

## 26. Deduplication

Products may appear:

- on the retailer site
- on Google Shopping
- through an affiliate page
- on a marketplace
- under slightly different titles

Deduplicate using:

- canonical URL
- retailer + SKU if available
- normalized title
- image similarity later if needed
- brand + model

Prefer the most authoritative source as the canonical candidate.

---

## 27. Source-quality hierarchy

Prefer:

1. manufacturer page
2. authorized retailer
3. major reputable retailer
4. recognized marketplace listing
5. affiliate / editorial page
6. unknown reseller

Source quality should affect confidence and ranking.

Do not ban lower-quality sources entirely if they reveal a promising product, but verify important facts elsewhere when possible.

---

## 28. Delivery logic

Delivery is one of the strongest opportunities for differentiation and one of the easiest places to lose trust.

V0 rules:

- location must be part of delivery evaluation
- distinguish "ships by" from "arrives by"
- distinguish made-to-order lead time from in-stock lead time
- quantity can affect availability
- if exact delivery cannot be verified, mark it unknown
- do not infer deadline success from generic site language

---

## 29. Budget logic

Normalize:

- per item
- total budget
- set price
- sale price
- list price
- quantity

Example:

Six chairs at max $350 each means:

- per-item cap = $350
- implied product subtotal cap = $2,100 before tax/shipping unless user says otherwise

If a product is sold as a set of two, normalize the effective per-chair price.

---

## 30. Dimensions logic

Dimensions should support item-specific semantics.

Dining chairs:

- overall width
- overall depth
- overall height
- seat height
- arm height
- seat width

Sofas:

- width
- depth
- height
- seat depth
- seat height
- clearance
- sectional orientation

Do not assume `width x depth x height` alone is enough for every product category.

---

## 31. V0 screens

### A. New sourcing request

Sections:

1. Item
2. Reference image
3. What I want
4. Budget
5. Dimensions
6. Location
7. Delivery deadline
8. Must-haves
9. Avoid

Primary CTA: **Find 5 options**

### B. Searching state

Show meaningful progress states:

- understanding request
- searching
- checking product details
- ranking options

Avoid fake precision.

### C. Results

Five product cards.

Provide:

- fit explanation
- verified facts
- uncertainty
- save / reject / open

### D. Replace result

User rejects one option.

System uses rejection reason to find a replacement without restarting the whole request.

### E. Request history

Minimal list of prior sourcing requests.

---

## 32. UX principles

- result quality over result quantity
- show five, not fifty
- disclose uncertainty
- keep source links visible
- make rejection useful
- let users write naturally
- avoid filter overload
- do not make the user re-enter context
- do not hide hard-constraint failures
- do not overstate AI confidence
- desktop comparison should feel excellent

---

## 33. Analytics / instrumentation

Track:

### Request level

- request created
- search started
- search completed
- search failed
- total candidates retrieved
- candidates after dedupe
- candidates after hard filters
- time to results

### Result level

- result shown
- retailer link opened
- saved
- rejected
- rejection reason
- replacement requested

### V0 evaluation

Add a deliberate evaluator after results:

"How useful were these results compared with how you normally source?"

Potential scale:

- much worse
- worse
- about the same
- better
- much better

Also ask:

"How many of these five would you seriously consider for the project?"

0–5.

---

## 34. Recommended V0 success criteria

These are recommended test thresholds, not immutable product doctrine.

Test across roughly 10–20 real sourcing requests with the target user.

A strong signal would be:

- average of at least 3/5 results rated as serious contenders
- majority of tested requests rated better than the user's normal Google/Pinterest process
- low rate of hard-constraint violations
- designers trust the factual details enough to open the retailer page
- rejection reasons improve replacement quality

The critical metric is not clicks. It is **decision usefulness**.

---

## 35. Test cases

### Test 1 — Existing dark walnut dining table

**Existing item:** Dark walnut dining table  
**Need:** 6 dining chairs  
**Style:** Scandinavian, warm, slightly vintage  
**Budget:** Maximum $350 per chair  
**Dimensions:** Must fit comfortably around the table  
**Location:** Los Angeles  
**Do not want:** Bouclé, black metal legs, very bulky chairs

Expected behavior:

- warm wood / natural materials
- visually lighter than table
- no excluded materials/leg type
- normalize set pricing
- explain relationship to walnut
- flag unknown fit dimensions if table measurements are missing

### Test 2 — Narrow apartment sofa

**Item:** Sofa  
**Reference:** Soft, relaxed European-looking sofa  
**Want:** Comfortable, elevated, not boxy  
**Budget:** Maximum $3,000  
**Dimensions:** Maximum 84 in wide; ideally 36 in deep or less  
**Location:** Los Angeles  
**Delivery:** Within 5 weeks  
**Must-have:** Neutral upholstery, removable or cleanable covers preferred  
**Bad result:** Deep 40+ in lounge sofas, bright white, obvious modular seams, low-quality marketplace listings

Expected behavior:

- depth is a hard gate
- delivery is important
- distinguish cleanable from removable covers
- reject 90+ in visually similar sofas

### Test 3 — Bedside tables around an existing bed

**Existing item:** Upholstered oatmeal king bed with rounded corners  
**Need:** Pair of nightstands  
**Style:** Warm modern, sculptural, not trendy  
**Budget:** Maximum $1,200 total  
**Dimensions:** 24–30 in wide; height should be appropriate for a standard king mattress setup  
**Location:** Los Angeles  
**Do not want:** Matching oatmeal fabric, mirrored finishes, black metal, fluted-front trend pieces

Expected behavior:

- recommend contrast, not literal matching
- sold-as-pair vs per-item budget normalization
- flag height uncertainty if bed/mattress height is missing

### Test 4 — Counter stools

**Item:** 4 counter stools  
**Want:** Warm natural materials, visually light, comfortable backs  
**Budget:** Maximum $450 per stool  
**Dimensions:** Counter-height seating; avoid overly wide stools  
**Location:** Los Angeles  
**Delivery:** Within 4 weeks  
**Must-have:** Backrest, footrest, durable seat  
**Bad result:** Bar-height stools, boucle, chrome, bulky upholstered bases, backless stools

Expected behavior:

- distinguish counter height from bar height
- footrest and backrest are hard constraints
- quantity-aware availability if data is available

---

## 36. What Codex should build first

### Phase 0 — Repo foundation

- initialize web app
- TypeScript strict mode
- linting / formatting
- environment validation
- database setup
- auth shell
- storage shell
- test framework
- analytics event abstraction
- provider interfaces

### Phase 1 — Thin vertical slice

Build one end-to-end happy path:

1. user creates request
2. request is normalized
3. search provider returns candidate products
4. candidates are normalized
5. scorer ranks them
6. five result cards render
7. user can save or reject

Use mocked candidate data first if necessary to validate architecture.

### Phase 2 — Live retrieval

- connect real search source
- evidence capture
- dedupe
- field normalization
- verification layer

### Phase 3 — AI reasoning

- structured constraint extraction
- image analysis
- compatibility reasoning
- explanation generation

### Phase 4 — Replacement loop

- reject
- reason
- re-rank / retrieve replacement
- persist feedback

### Phase 5 — V0 test instrumentation

- comparison survey
- contender count
- hard-constraint violation review
- latency and cost logging

Do not start with voice, AR, or camera.

---

## 37. Engineering principles for Codex

- read `AGENTS.md` before work
- treat `/docs` as source of truth
- keep scope V0-small
- prefer explicit types
- validate all AI outputs
- use structured outputs / schemas
- isolate external providers behind interfaces
- do not make live commerce claims without evidence
- preserve provenance for product facts
- separate hard filters from ranking
- test budget and dimension normalization
- test negative constraints
- log enough to debug why a product ranked
- build replacement as a first-class flow
- no giant "AI magic" function

---

## 38. Security and privacy

V0 should still:

- keep secrets server-side
- validate uploads
- enforce file-size limits
- restrict accepted file types
- use signed/private storage when appropriate
- use row-level access controls
- avoid logging private image contents unnecessarily
- sanitize URLs and external content
- treat external page content as untrusted
- protect against prompt injection in scraped/search content
- never execute arbitrary content from product pages
- rate-limit expensive search/AI endpoints

External web content must be treated as data, not instructions.

---

## 39. Cost controls

Track per request:

- search provider calls
- AI calls
- input/output tokens if applicable
- verification fetch count
- total latency

Useful controls:

- cache normalized candidates
- cache product verification for a short TTL
- only deeply verify likely top candidates
- use cheaper models for extraction when quality is sufficient
- reserve strongest reasoning for final ranking/explanation if needed

Do not optimize cost before quality is measurable, but instrument it from day one.

---

## 40. Failure states

Handle:

### No five valid products

Return fewer than five rather than knowingly violating a hard constraint.

Tell the user which constraint is limiting results.

### Conflicting constraints

Example:

- max width 22 in
- wants oversized lounge chair

The system should surface the conflict.

### Missing critical detail

If exact fit cannot be proven, return candidates with a visible warning rather than inventing the answer.

### Provider outage

Persist the request and show a clear retry state.

### Bad AI parse

Schema validation should fail closed and retry / fallback.

---

## 41. Non-goals for recommendation intelligence

Do not claim the system:

- has human taste
- knows unseen inventory
- guarantees delivery
- guarantees stock
- guarantees exact colors from photos
- guarantees compatibility from one reference image

The product should be useful because it combines evidence and reasoning well.

---

## 42. Product moat hypothesis

Potential moat is not "LLM + search."

Potential moat comes from:

- structured purchasing context
- project-specific negative constraints
- compatibility reasoning
- factual verification
- designer feedback
- sourcing outcome data
- ranking tuned to real designer decisions
- eventually, memory across projects / clients / vendors with appropriate controls

V0 only needs to test the first part.

---

## 43. Future roadmap — after V0 proves itself

Possible later layers:

1. project-wide context
2. client preferences
3. room context
4. trade pricing
5. vendor relationships
6. collaborative shortlists
7. procurement
8. live voice
9. live camera
10. native mobile apps
11. browser extension
12. client presentation / approvals
13. purchase tracking
14. automated replacements when items go out of stock

Do not prebuild these into V0 beyond sensible extensibility.

---

## 44. Open questions to resolve during development

These do not block kickoff.

### Product data

- Which search/product providers give the best furniture coverage?
- How much retailer-page verification is needed?
- What is the compliant approach for each source?

### Delivery

- Can a provider return destination-aware delivery estimates?
- When do we ask the user for ZIP code rather than city?
- How do we handle white-glove freight?

### Images

- Can product images be displayed directly from retailer/CDN URLs under source terms?
- Should the system proxy/cache thumbnails?

### Auth

- Email magic link vs social login for V0?

### User testing

- Which 5–10 designers will be first testers?
- What categories should the evaluation set cover?

### Business model

Not required for development kickoff. Do not distort V0 around monetization yet.

---

## 45. Definition of done for first usable V0

A real interior designer can:

1. sign in
2. create a sourcing request
3. upload a reference image
4. enter all major constraints
5. run a search
6. receive five ranked, sourced product recommendations
7. see why each fits
8. see uncertainty / warnings
9. open retailer pages
10. save or reject results
11. request a replacement
12. rate whether the result set beat their usual process

The development team can inspect:

- parsed constraints
- candidates
- filtered candidates
- scores
- evidence
- user feedback
- latency
- cost

---

## 46. First Codex task

Paste this into Codex after placing the package in the repository:

> Read `AGENTS.md`, then `CODEX_START_HERE.md`, then the documents it links. Treat the docs as the product source of truth. Start with Phase 0 and Phase 1 only. Create the smallest working vertical slice of the responsive web app. Do not build voice, camera, AR, procurement, checkout, native mobile apps, or other future features. Use provider interfaces for AI, search, verification, storage, and analytics so external services can be swapped. Use strict TypeScript, schema validation, tests for core normalization/filtering/ranking logic, and clear loading/error states. Before making major product assumptions, check `docs/DECISIONS.md` and `docs/OPEN_QUESTIONS.md`. Record any new architectural decision in `docs/DECISIONS.md`.

---

## 47. Important context about prior visual assets

Previous project conversations included requests for generated explanatory visuals, including a visual about voice/camera use.

Those prior generated image binaries are **not available inside this current chat's file workspace**, so they cannot be reliably bundled here without inventing replacements.

This package therefore includes:

- the complete text equivalent of the relevant voice/camera concept
- an `assets/reference-images/README.md` manifest
- placeholders for the prior visual files

To preserve the exact previous visual assets, export/download them from their original project conversation and place them into `assets/reference-images/`.

Do not let missing visuals block V0 engineering.

---

## 48. Final product guardrail

When deciding whether to add something, ask:

> Does this materially help us test whether an AI agent can produce five more useful, purchase-ready furniture recommendations than the designer's normal sourcing process because it understands the full context?

If not, it probably does not belong in V0.

# V0 Test Cases

## Test 1 — Dark walnut table / six dining chairs

- Existing item: Dark walnut dining table
- Need: 6 dining chairs
- Style: Scandinavian, warm, slightly vintage
- Budget: maximum $350/chair
- Dimensions: must fit comfortably around table
- Location: Los Angeles
- Exclusions: bouclé, black metal legs, very bulky chairs

Assertions:

- excluded features never appear in confirmed product facts
- per-chair prices normalize correctly
- result explanation discusses compatibility with dark walnut
- system does not claim dimensional fit without table dimensions

## Test 2 — Narrow apartment sofa

- Item: sofa
- Want: soft, elevated, European feel, not boxy
- Budget: max $3,000
- Max width: 84 in
- Preferred max depth: 36 in
- Location: Los Angeles
- Delivery: within 5 weeks
- Preferred: neutral, removable/cleanable cover
- Exclusions: 40+ in deep lounge sofas, bright white, obvious modular seams, weak marketplace sources

Assertions:

- width over 84 in fails
- depth is correctly interpreted
- delivery uncertainty is visible
- "cleanable" is not rewritten as "removable"

## Test 3 — Nightstands around oatmeal bed

- Existing item: oatmeal upholstered king bed, rounded corners
- Need: pair of nightstands
- Style: warm modern, sculptural, not trendy
- Budget: max $1,200 total
- Width: 24–30 in each
- Location: Los Angeles
- Exclusions: matching upholstery, mirrored, black metal, fluted-front trend pieces

Assertions:

- total budget normalizes to pair context
- recommendations may use contrast
- system warns if target nightstand height cannot be confirmed without bed/mattress height

## Test 4 — Counter stools

- Item: 4 counter stools
- Budget: max $450/stool
- Location: Los Angeles
- Delivery: within 4 weeks
- Must-have: counter height, backrest, footrest, durable seat
- Style: warm natural materials, visually light
- Exclusions: bar height, bouclé, chrome, bulky upholstered bases, backless

Assertions:

- bar-height is rejected
- backless is rejected
- no missing required backrest/footrest
- quantity-aware availability is displayed only when known

## Unit-test categories

- money parsing
- set/per-item price normalization
- dimension parsing
- unit conversion
- hard exclusions
- unknown field propagation
- source-quality scoring
- duplicate detection
- diversity
- feedback-to-replacement constraints

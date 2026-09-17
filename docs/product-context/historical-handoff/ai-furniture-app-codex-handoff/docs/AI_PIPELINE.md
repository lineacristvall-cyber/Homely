# AI / Search Pipeline

## Principle

Use AI to interpret and reason. Use evidence-bearing sources for commerce facts.

## Stages

1. Parse request.
2. Extract structured constraints.
3. Classify hard vs soft.
4. Analyze reference image.
5. Generate multiple search-query families.
6. Retrieve broad candidates.
7. Normalize.
8. Deduplicate.
9. Verify high-value candidates.
10. Filter hard failures.
11. Score soft fit.
12. Apply diversity.
13. Generate explanations from verified facts.
14. Return top five.
15. Learn from feedback for replacements.

## Hard constraints

Examples:

- item type
- budget maximum
- dimension maximum/minimum
- excluded material
- excluded finish
- required feature
- destination shipping
- delivery deadline

## Soft preferences

Examples:

- style
- era
- visual weight
- warmth
- "slightly vintage"
- "not too trendy"
- similarity to reference image
- compatibility with existing item

## Verification states

- confirmed
- observed
- inferred
- unknown
- conflicting

## Ranking

Hard constraints are gates.

Suggested initial soft score:

```text
0.30 visual/style fit
0.20 functional fit
0.15 existing-item compatibility
0.15 budget fit
0.10 dimension fit
0.05 delivery confidence
0.05 source quality
```

Make weights configurable.

## Diversity

Avoid five near-identical results.

Diversity can consider:

- brand
- silhouette
- price point
- material
- retailer
- visual interpretation

All diverse results still must remain on-brief.

## Replacement

When the user rejects an item:

- store reason
- transform reason into request-specific negative signal
- remove rejected/near-duplicate candidates
- re-rank existing valid candidates
- retrieve more candidates if needed
- return one replacement

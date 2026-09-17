# Data Model

## Core entities

- users
- sourcing_requests
- reference_images
- normalized_constraints
- product_candidates
- verified_products
- product_evidence
- recommendations
- recommendation_feedback
- request_evaluations

## Suggested tables

### sourcing_requests

- id
- user_id
- mode
- item_needed
- what_i_want
- budget_json
- dimensions_json
- location_json
- delivery_deadline
- must_haves_json
- dislikes_json
- existing_item_json
- status
- created_at
- updated_at

### reference_images

- id
- request_id
- storage_url
- mime_type
- analysis_json
- created_at

### normalized_constraints

- id
- request_id
- type
- value_json
- hardness
- confidence
- source_text

### product_candidates

- id
- request_id
- canonical_url
- title
- retailer
- image_url
- source_type
- raw_json
- dedupe_key
- created_at

### verified_products

- id
- candidate_id
- normalized_product_json
- verification_summary
- verified_at

### product_evidence

- id
- candidate_id
- field_name
- value_json
- state
- source_url
- observed_at
- notes

### recommendations

- id
- request_id
- candidate_id
- rank
- fit_score
- score_breakdown_json
- reasons_json
- warnings_json
- confidence
- created_at

### recommendation_feedback

- id
- request_id
- candidate_id
- action
- reason
- free_text
- created_at

### request_evaluations

- id
- request_id
- usefulness_vs_normal
- serious_contenders_count
- notes
- created_at

## Important modeling rule

Do not store one mutable blob as the only record of the recommendation process. Preserve enough intermediate state to debug:

- what the user said
- what the model extracted
- what search returned
- what was verified
- what was filtered
- why something ranked

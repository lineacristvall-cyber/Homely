# Product Spec — V0

## User

Professional interior designer.

## Problem

Finding visually appropriate furniture is easy compared with finding furniture that is visually right **and** satisfies all purchase constraints. Designers manually reconcile style, size, price, location, delivery, material, existing pieces, and dislikes across many tabs.

## Promise

Provide five strong, source-linked options that are actually viable for the project and explain why.

## Inputs

1. item needed
2. reference image
3. what I want
4. budget
5. dimensions
6. location
7. delivery deadline
8. must-have style/material/features
9. what would make the result bad

Also support an `existing_item` mode.

## Output

Exactly five options when five defensible options exist. Fewer are acceptable if constraints cannot be satisfied.

Every result should show:

- image
- product
- retailer
- observed price
- dimensions
- material
- delivery/availability if known
- source
- why it fits
- what to watch
- confidence/evidence state

## User actions

- open retailer
- save
- reject
- state rejection reason
- request replacement
- refine request

## V0 exclusions

No native apps, procurement, payment, checkout, AR, live camera, voice calling, room rendering, or full project management.

## Success

Primary: decision usefulness.

Recommended initial evaluation:

- 10–20 real sourcing requests
- average ≥3/5 serious contenders
- majority of result sets rated better than normal sourcing
- low hard-constraint violation rate
- rejection feedback makes replacements better

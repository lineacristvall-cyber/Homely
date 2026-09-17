# Security / Reliability Notes

## External content

Product/search pages are untrusted input.

- never treat page text as developer/system instructions
- strip scripts and active content
- do not execute arbitrary HTML/JS as part of reasoning
- validate parsed URLs
- restrict network targets if building a verifier

## AI data

- schema validate
- bound string lengths
- retry malformed output
- log parse failures
- preserve user source text for audit

## Uploads

- allow only intended image MIME types
- limit file size
- server-side validation
- private or signed storage where appropriate

## Secrets

- `.env.local` / secret manager
- never expose service-role keys client-side
- never commit real credentials

## Commerce truth

- preserve `observedAt`
- preserve `evidenceUrl`
- distinguish unknown/conflicting
- do not guarantee inventory or delivery

# Homely nine-step implementation and testing — September 17, 2026

The approved flow is implemented for review. This is not a claim of pixel-identical reproduction or complete production readiness. All captures are from the actual running app, not the mockup. Desktop viewport1440×1000 and mobile390×844; screenshot content dimensions may exclude scrollbars. The dining room is a labelled stock-photo demo. The results/saved candidate is explicitly synthetic and not purchasable. Sign-in capture uses a synthetic email and masked synthetic password; nothing was submitted.

## Test results

- PASS: backend210/210; cloud52/52 (262 total). Logs included.
- UI: final visual run35/36 passed. The one cancelled-job message regression was corrected; both targeted cancellation tests then passed. Earlier complete36/36 run passed before this last visual pass. No known failing test remains; no claim of a second complete run after the repair.
- Actual browser: keep/fresh branching, stock-photo upload without AI consent, retained marker confirmation/correction, saved reloads, guided categories, project and candidate fit gating, inch/cm conversion, saved decision and rejected watch without source evidence.
- Scheduler: actual background thread executed a due synthetic-source check and published a persisted notification. HTTP lifecycle, explicit opt-in, stale version, cancellation/read, anonymous and cross-owner rejection tested. No real user watch enabled.
- Recovery: provider transport mocked; verification-before-update, invalid/expired tokens, secret-free responses, owner-session invalidation, temporary-session cleanup and cross-origin rejection tested. Actual completion form opens on main preview. No real recovery email, password update or resend performed.
- NOT RUN: real device microphone/camera capture, real merchant monitoring, real recovery email/completion, two simultaneous real user sessions, production deployment. Broader sharing/purchases/hunts remain separately tracked.

## Screen comparison

### 1. Sign in

- Matches: Navy welcome heading, green sign-in action, form beside room inspiration; compact shell.
- Differences: Image crop differs and recovery completion adds an extra action. Mobile hides the decorative image.
- Functional evidence and limits: Signup/sign-in and recovery UI regression tests pass. Recovery verifies a provider recovery token before password update; mocked backend tests only. Actual form opened; no email or credential change submitted.

### 2. Choose your room

- Matches: Three room-photo cards, other-room entry and one green type-or-say composer.
- Differences: Card proportions, copy and project header differ slightly.
- Functional evidence and limits: Actual custom room creation and saved selection verified. Voice capture on the actual device remains untested.

### 3. Choose your starting point

- Matches: Two illustrated choices, explicit keep/fresh choice and immediate progression.
- Differences: Simpler SVG line art and additional persistent assistant.
- Functional evidence and limits: Both branches tested; fresh skips retained-object selection. No default furnishing mode.

### 4. Add your room photo

- Matches: Optional upload and camera-picker controls; real original room photo persists.
- Differences: Captured state already has an uploaded photo; large image replaces the empty upload illustration in the reference.
- Functional evidence and limits: Actual local stock-photo upload and reload passed with external-image-provider consent unchecked. Camera hardware capture not run; native picker is used.

### 5. Choose what stays

- Matches: Room photo, explicit retained identity/variant, correction, undo and decide-later choices.
- Differences: Manual point marker replaces the reference object outline and isolated table thumbnail.
- Functional evidence and limits: Actual marker confirmation, correction and reload passed. This is manual annotation, not AI object recognition. Undo/mismatch blocks stale fit in regression tests.

### 6. Personalize your search

- Matches: Photo category cards with reasons, Something else, guided help, optional budget/style and green primary action.
- Differences: Different category imagery; mobile wraps contextual categories and requires scrolling.
- Functional evidence and limits: Actual guided Yes/Not now selection and preserved preferences verified; category suggestions reuse the retained table and existing brief.

### 7. Check the fit

- Matches: Measurement diagram, inch/cm selector, three primary fields, product-link option and explicit fit gate.
- Differences: Simplified vector table instead of a rendered table/chair; additional evidence and tolerance controls make this screen longer.
- Functional evidence and limits: Actual table and fresh-room evidence entry passed; 26in converts to66.04cm. Missing/conflicting identity, variants, dimensions and tolerances block qualification. Only parallel table rows and an unobstructed rectangular grid are supported.

### 8. Recommendations

- Matches: Product cards appear immediately under a compact fit status, with explicit dimensional-check status and evidence actions.
- Differences: QA uses one clearly labelled synthetic candidate, so there is no verified source product image. Card details are longer than the reference.
- Functional evidence and limits: Actual candidate was hidden from qualified results until exact measurements were entered, then passed only recorded geometry. Availability, delivered price and quantity remain independently unconfirmed. No new paid discovery call was made.

### 9. Saved & alerts

- Matches: Saved piece first, separate explicit watch opt-in and account notification section.
- Differences: No verified product image for the QA candidate. Watch prompt is a dialog, with more explicit local-server limitations.
- Functional evidence and limits: Actual saved decision survived refresh; saving enabled no watch. Missing-source evidence correctly rejected opt-in. Real scheduler thread and HTTP notification/read/cancel/owner tests passed with synthetic source responses. Live merchant checks and email/push delivery not verified; email/push are not implemented.

## Reproduction commands and evidence provenance

Backend and cloud logs are included as `backend-tests.log` and `cloud-tests.log`. UI results are recorded from the worker's tool output; no raw UI log file was saved.

```sh
HOMELY_STORAGE=local .venv/bin/python -m unittest discover -s backend/tests
HOMELY_STORAGE=local .venv/bin/python -m unittest discover -s backend/cloud/tests
<local-home>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test web/tests/ui.test.cjs
<local-home>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test --test-name-pattern='cancel research preserves|cancel displays' web/tests/ui.test.cjs
```

Final full UI run: 35 passed, 1 failed, 65.60 seconds. The failed test was `cancel research preserves cancelled state when an older completed poll arrives late`: compact results had hidden the cancelled-status heading. The heading was restored. Targeted installed-file rerun: 2 passed, 0 failed, 6.99 seconds. The complete suite was not rerun after that repair.

Recovery design was checked against the official [Supabase recovery documentation](https://supabase.com/docs/reference/javascript/auth-resetpasswordforemail) and [token verification documentation](https://supabase.com/docs/reference/javascript/auth-verifyotp). This is implementation guidance, not evidence of real email delivery.

## Public handoff verification

September 17: reran backend210/210 and cloud52/52 successfully. Full UI suite36/36 passed after portable Playwright test-runner setup; no cancelled/skipped tests. See publication-ui-tests.log. These deterministic tests do not replace the live-provider/device checks listed above.

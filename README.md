# Homely

Homely is a loopback-only interior sourcing POC with a Python HTTP server, vanilla browser UI, Supabase email/password authentication, user-owned cloud projects and private images. Product requirements are in [current context](docs/product-context/CURRENT_CONTEXT.md); [PROGRESS.md](PROGRESS.md) records acceptance evidence and [OPEN_ACTION_ITEMS.md](OPEN_ACTION_ITEMS.md) records remaining work. The [architecture reference](docs/product-context/architecture/ARCHITECTURE_REFERENCE-v2.md) describes the intended system, including capabilities still pending.

## Developer quick start

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
HOMELY_STORAGE=local HOMELY_PORT=8768 python -m backend.server
```

Open http://127.0.0.1:8768/. Local mode runs without credentials and stores private runtime data in ignored `data/`. For the reproducible stock-photo demo, run `python fixtures/dining-room-stock-v1/preview.py --help` and use its documented options. Cloud mode requires separately supplied configuration; no credentials or user uploads are included in this repository.

```sh
npm install
npx playwright install chromium
npm run test:ui
```

See [DEVELOPER_HANDOFF.md](DEVELOPER_HANDOFF.md) for the documentation map, current limitations, and public-release exclusions.

## Run the local preview

Run from the repository root with Python 3.10+ and Pillow. On this development machine, the bundled interpreter already includes Pillow:

```sh
HOMELY_PYTHON=.venv/bin/python
HOMELY_PORT=8766 "$HOMELY_PYTHON" -B -m backend.server
```

Open <http://127.0.0.1:8766/>; the acceptance tracker is at `/progress`. Port defaults to 8765 without `HOMELY_PORT`. Use one server process for this data directory. The server binds to `127.0.0.1` and rejects foreign Host/Origin values; it is not publicly deployed or ready to expose through a proxy/tunnel.

The existing ignored `.env.local` selects `HOMELY_STORAGE=cloud` and contains server-only configuration. Do not overwrite it. For a new checkout, set `HOMELY_STORAGE=cloud`, the approved project's `SUPABASE_PUBLISHABLE_KEY`, and `OPENAI_API_KEY` through the process environment or an ignored `.env.local` containing plain `NAME=value` lines without shell quotes or `export`. Process environment values take precedence. Never commit or print credentials. The running server fixes the Supabase origin to the approved project; see [cloud setup](backend/cloud/README.md).

Sign up or sign in through Homely's email/password UI; complete email confirmation when required. Access/refresh tokens remain server-side and the browser receives an opaque HttpOnly, SameSite=Strict session cookie. **Restarting the server signs users out**, while cloud projects and uploaded assets persist. Sessions expire after 30 minutes idle or eight hours total.

For the separate local JSON/files workspace, launch explicitly with `HOMELY_STORAGE=local` added to the command. Local mode is an unauthenticated, single-user development workspace. Switching modes neither imports local records into a cloud account nor falls back to local data after a cloud failure. Preserve `data/`; no automatic migration is implemented.

## Runtime capabilities and limits

- Source research uses server-side OpenAI Responses web discovery, then at most two public-page enrichments. URL import extracts structured product information with robots, public-network, time and size checks. Coverage records actual discovery/enrichment calls and blocked/failed attempts; provider-internal website attempts are unavailable and coverage is always incomplete.
- Candidates remain research leads unless fresh, attributable exact-variant quantity and delivered-cost evidence passes server gates. No merchant stock adapter is registered. Facebook Marketplace, Craigslist and eBay integrations are unsupported; a visible product page does not establish stock or image-generation rights.
- Typed assistant proposals are grounded in the current project and applied through confirmation/version checks. Voice records with consent and offers an editable transcript. Real synthetic speech transcription and confirmed action persistence passed; actual device microphone capture remains pending.
- Visualization requires room consent and an actual product reference with confirmed rights. Output is illustrative; product fidelity and measured fit require separate checks. Real synthetic image edits, app generation and rerender passed. Merchant SKU identity, distinct-product swap and cloud generation acceptance remain pending.

Current source defaults are `gpt-5.6-luna` for research and assistant planning, `gpt-transcribe` for transcription, and `gpt-image-2.5-flare` for image edits. These are configured code values, not a claim that every live path is verified. Export `HOMELY_RESEARCH_MODEL`, `HOMELY_ASSISTANT_MODEL` or `HOMELY_TRANSCRIPTION_MODEL` in the **process environment** to override their defaults; assistant defaults to the research override when its own is unset. These module overrides and `HOMELY_PORT` are not loaded from `.env.local`. The image model is currently a constant in `backend/visualization.py`.

## Verification

Run deterministic backend and cloud tests from the repository root, explicitly overriding the configured cloud mode. These commands use mocks/temporary data and do not constitute live provider or deployed isolation acceptance:

```sh
HOMELY_PYTHON=.venv/bin/python
HOMELY_STORAGE=local "$HOMELY_PYTHON" -B -m unittest discover -s backend/tests -v
HOMELY_STORAGE=local "$HOMELY_PYTHON" -B -m unittest discover -s backend/cloud/tests -v
```

Recorded live acceptance includes cited research/public URL import, one typed quantity proposal with confirmation and reload, email signup/confirmation/sign-in, cloud project save/reload, and private synthetic room upload/reload. Anonymous access to that private asset returned 401. Deployed rollback-only SQL role-isolation assertions passed; **two real users with separate JWT sessions have not been tested**.

Background jobs still run in this server's daemon threads, with owner-scoped files under `data/private-cloud-jobs` and image working files under `data/private-cloud-cache`. They are separate from local-mode jobs/assets, but are not a durable cloud queue: process restart does not resume work, and authenticated cloud job writes remain pending. Public hosting, distributed sessions/workers, cross-user sharing, hunts and privacy deletion remain unfinished. Owner-scoped JSON export is implemented with bounded pagination and no partial truncation; the actual local download passed. Export excludes image files, jobs, audio, account settings and unsaved drafts. See the [cloud guide](backend/cloud/README.md) for deployed scope and remaining isolation checks.


## Guided nine-step review
The current guided flow includes room choice, keep/fresh branches, optional room upload, confirmed manual retained-piece markers, contextual categories, strict dimensional fit evidence, qualified-result filtering and saved decisions. Inch/cm changes convert dimensions. Upload permission and optional external-image-processing consent are separate.

Review the [screen comparison](artifacts/nine-step-flow-2026-09-17/index.html) and [testing report](artifacts/nine-step-flow-2026-09-17/TESTING_REPORT.md). Local preview:8766 (cloud/sign-in),8768 (stock-photo demo),8773 (comparison). Choose the project menu then New room to begin from room selection; existing projects retain their saved step.

Recovery is explicit: request an email, copy its unopened recovery link into **Have a recovery email?**, and submit your new password yourself. The server verifies the token as recovery and discards its temporary session; already-used links need a new email. This code path is covered with mocked provider tests; real delivery/completion is not yet verified.

Price watches require separate opt-in on a saved current product with fresh exact-SKU/variant/price evidence. They persist privately and run hourly only while this local server is running. Updates appear in Saved; no email/push or hosted availability promise. General saved research hunts remain unfinished. No watch starts just because an item is saved.

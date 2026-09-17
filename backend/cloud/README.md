# Homely cloud workspace

The existing **FREE** Supabase project `bbwmwwupvqajidqznsly` is connected to the local Homely POC. The transactional migration deployed `public.homely_projects`, `public.homely_jobs`, `public.homely_assets` with forced owner RLS and the private `homely-private-assets` bucket. No local records were migrated, and no paid plan, add-on, project or branch was created.

## Recorded acceptance and remaining gates

The authenticated dashboard confirmed the schema and private bucket configuration. The rollback-only [SQL isolation suite](tests/isolation.sql) passed owner, anonymous, job-forgery and storage assertions; follow-up verification found no remaining fixtures. This exercises database roles, not two independent application JWT sessions.

Real email signup, confirmation and sign-in passed. A clearly labeled cloud acceptance project/brief persisted after full browser reload. A private synthetic room image uploaded and rendered after reload through `/api/cloud-assets/{id}`; an anonymous request for that same asset returned 401. No image-generation provider was called for this check. **Two real-user JWT project/asset isolation tests remain pending.** See the latest appended evidence in [PROGRESS.md](../../PROGRESS.md).

## Configuration and startup

Use the [root startup instructions](../../README.md) from the repository root. The existing ignored `.env.local` already selects cloud mode and holds configured keys; do not replace it or copy its contents into logs, chat or commits.

| Configuration | Current contract |
| --- | --- |
| `HOMELY_STORAGE=cloud` | Enables authenticated cloud project/private-image storage; process environment overrides `.env.local`. |
| `SUPABASE_PUBLISHABLE_KEY` | Approved project's `sb_publishable_...` key, supplied server-side. Secret/service-role keys are rejected by this adapter. |
| Project origin | `https://bbwmwwupvqajidqznsly.supabase.co`; fixed by the integrated server and validated by `CloudSettings`. |
| `SUPABASE_URL` | Accepted by standalone `CloudSettings.from_environment()` only; must equal the approved origin. The current HTTP server uses the fixed origin directly. |
| `OPENAI_API_KEY` | Separate server-only key for sourcing, assistant/transcription and visualization calls. Not required to establish Supabase authentication. |

No database password or service-role key is needed for the current application. Email/password authentication uses the existing project settings. The browser receives an opaque HttpOnly, SameSite=Strict cookie, never access/refresh tokens in JSON. `AuthManager` validates real tokens with `/auth/v1/user`, serializes refresh-token rotation, and scopes each request to the signed-in user. Sessions are in memory: server restart signs everyone out; default idle/absolute limits are 30 minutes/eight hours.

The HTTP server runs only on loopback, with exact local Host/Origin checks and HTTP preview cookies. There is **no public deployment**. HTTPS/Secure-cookie integration, production origin configuration, persistent/distributed sessions and a durable worker service must be designed before public hosting; placing this preview behind a proxy is not a deployment procedure.

## Deployed SQL and repeatable verification

The existing deployment used the authenticated [project dashboard](https://supabase.com/dashboard/project/bbwmwwupvqajidqznsly), not callable MCP tools. No reapplication is needed to use it. For an authorized schema recheck:

1. Confirm the project identity and FREE plan in the dashboard. Inspect existing tables and bucket before changing anything.
2. Review [001_homely_private_workspace.sql](migrations/001_homely_private_workspace.sql). It is transactional and rerunnable for its own schema version, adds the Homely schema without importing local data, and aborts on incompatible existing bucket settings rather than silently changing privacy/limits. Do not assume it upgrades an arbitrary schema.
3. Run [tests/isolation.sql](tests/isolation.sql) in SQL Editor when repeating deployed role-isolation validation. It creates temporary fixture identities/data, impersonates authenticated roles, checks denials and rolls back. Record the actual result; a fixture UUID collision aborts rather than overwriting an account.
4. Complete the still-pending test with two real users in independent browser sessions: B must not list/read/update A's project or read A's private asset. Verify anonymous denials and stale-version conflicts. SQL-role and mocked HTTP tests do not substitute for this acceptance.

Official project-scoped MCP OAuth succeeded with narrow database/storage access. Callable tools remained unavailable in both the current session and a bounded fresh CLI check, so the dashboard was used. Do not describe MCP as an available application integration or request broader account/branching permissions to work around this limitation. MCP is developer tooling; the app uses Auth/REST/Storage HTTP endpoints.

## Integrated interfaces and data boundaries

- `AuthManager(settings).sign_in(email, password)` returns a private server session ID and safe user fields; `resolve(session_id)` returns the authenticated `CloudSession`, and `sign_out(session_id)` removes that local session. The HTTP layer puts only the opaque ID in the cookie. Signup follows the email-confirmation flow.
- `CloudProjectStore(session).list()/get(id)/create(project)/save(project)` maps the Homely document and `pro`/`diy` mode to database envelopes. The database/session determines owner, UUID, timestamps and version; JSON cannot overwrite those fields. Save filters the expected previous version and rejects conflicts. Mode is fixed at creation in this adapter.
- `upload(project_id, kind, raw, mime, consent, lineage)` stores immutable private assets and returns an app URL `/api/cloud-assets/{id}`. `read(asset_id)` authorizes and fetches from the approved Supabase HTTPS origin without redirects, returning bytes/MIME instead of leaking a signed URL. Images must decode as JPEG/PNG/WebP, up to 10 MiB and 25 million pixels. Upload consent and image-generation rights remain separate gates.
- `CloudSession` provides the lower-level owner-scoped REST adapter and short-lived signed asset reads. Upload failure may leave metadata without bytes; reconciliation is not automatic. No overwrite/delete or cross-user sharing workflow ships here.

The server attaches an authenticated owner context to requests and background work. Cloud-mode job files and image working files use `data/private-cloud-jobs` and `data/private-cloud-cache`, separate from local-mode directories. Jobs currently run in daemon threads and are filtered by owner; cloud job-table writes and restart recovery are not implemented. Supabase user clients have no job-write grant, and this adapter has no service-role bypass. Preserve these private working directories as user data; they are not a public static-assets directory.

Local JSON projects remain intact in explicit `HOMELY_STORAGE=local` mode. Cloud failures do not fall back to local/shared accounts, and switching modes does not migrate data. Any future copy/migration needs an explicit owner mapping and reviewable result.

Cloud project JSON is user-editable data, not trusted stock evidence. Exact-stock eligibility, provenance, delivered cost, image rights and sharing authorization still require independent server validation. Authentication and private storage do not establish source rights or a client-sharing system.

## Local tests

The transport/auth code uses the standard library; full application/image tests also require Pillow. On this development machine:

```sh
HOMELY_PYTHON=.venv/bin/python
HOMELY_STORAGE=local "$HOMELY_PYTHON" -B -m unittest discover -s backend/cloud/tests -v
HOMELY_STORAGE=local "$HOMELY_PYTHON" -B -m unittest backend.tests.test_cloud_routes backend.tests.test_jobs_recovery -v
```

These tests use mocks and temporary data, without live credentials or provider calls. They cover session refresh/isolation, owner predicates, optimistic conflicts, private image access, mode separation and stale/cancelled job publication. They do not prove real microphone transcription, live image generation, two-JWT isolation or public deployment readiness.

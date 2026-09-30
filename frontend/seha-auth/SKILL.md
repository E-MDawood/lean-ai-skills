---
name: seha-auth
description: >
  Use this skill to obtain a dev/test auth token for an app that is embedded as
  an iframe inside the SEHA platform, and write it into that project's local env
  file (e.g. VITE_DEV_TOKEN in environments/.env.development.local), so the app
  can be driven and screenshotted without going through SEHA's real login UI by
  hand. Trigger when a browser-driven check (e.g. the sprint-planning skill's UI
  validation step, or browser-check/run) is blocked needing SEHA authentication
  or a specific role, when the user asks to "get a token for <role>", "log in as
  <role> for testing", or references a SEHA users JSON file. Complementary to
  browser-check/run — this is the concrete answer to "what's the auth method"
  for SEHA-embedded projects specifically, not a replacement for them.
---

# SEHA Auth Skill

Drives SEHA's real login flow headlessly with Playwright to obtain a valid app
token for a given user/role, caches it for reuse within the same session, and
writes it into the target project's env file. Ported from the headed,
UI-driven flow in the sibling `seha-login-test-flow` project — same selectors,
same mechanics, but non-interactive and headless by default.

This skill is generic: it doesn't hardcode a project's service name, JSON
file, or URLs. Everything is either read from the project's own environment
files, asked once and remembered, or asked every time it's genuinely
ambiguous (see "Resolve which user" below).

---

## Step 1 — One-time setup (silent)

Check whether `scripts/node_modules/playwright` already exists inside this
skill's folder. If not, run once, without asking:

```bash
cd .claude/skills/seha-auth/scripts && npm install
```

`npm install`'s `postinstall` runs `playwright install chromium` automatically.
This installs Playwright + a Chromium binary self-contained inside the skill's
own folder — it never touches the consuming project's own `package.json` or
`node_modules`.

---

## Step 2 — Resolve project config

Config lives at `docs/seha-auth/config.json` in the **consuming project**
(not inside this skill's folder — every project using this skill gets its own
config). **Not gitignored** — it's small, useful shared context, and doesn't
change often, so it's meant to be committed (unlike `cache.json`, see Step 5).
Shape:

```json
{
  "serviceName": "منصة الاحالات",
  "sehaBaseUrl": "https://seha.devclan.io",
  "iframeUrlPattern": "rei.devclan.io",
  "loginPath": "/#/Account/Login",
  "otp": "1234",
  "envVarName": "VITE_DEV_TOKEN",
  "envFilePath": "environments/.env.development.local",
  "usersJsonPath": "docs/seha-auth/users.json"
}
```

If the file doesn't exist yet, or is missing a field, resolve each missing
field in this order before asking:

- `sehaBaseUrl` and `iframeUrlPattern` → **don't search for a specific
  variable name** — env var naming isn't standardized across projects, so
  there's no fixed name that's guaranteed to exist elsewhere. Instead, read
  the project's env files and use judgment to spot which ones plausibly hold
  each value: `sehaBaseUrl` is whichever URL-valued variable looks like it
  points at the SEHA platform itself (its name will likely mention "seha" in
  some form); `iframeUrlPattern` is the hostname of whichever variable holds
  *this app's own* base/API URL (strip protocol and any path, e.g.
  `https://rei.devclan.io/api` → `rei.devclan.io`). In referral-frontend
  today those happen to be `VITE_SEHA_WEB_URL` and `VITE_API_URL`
  respectively — treat that as one example of what this can look like, not a
  name to search for in a different project.
  - Once you've picked a candidate this way, **show the user what you found
    and what you're about to derive from it** (e.g. "found
    `VITE_API_URL=https://rei.devclan.io/api` in `environments/.env.development`,
    using `rei.devclan.io` as the iframe pattern — correct?") and get a yes
    before persisting it to config. This is a judgment-based guess, not an
    exact lookup, so it gets a one-time confirmation before being trusted —
    after that, it's remembered in the config like every other resolved
    field, no need to re-confirm on later runs.
  - If nothing in the env files looks plausible at all, skip the guess
    entirely and just ask directly.
- `loginPath` → default to `/#/Account/Login` if not otherwise specified, but
  don't treat this as fixed either. SEHA has (at least) two real login page
  variants — the default and `/#/Account/custom-Login` — and which one
  actually has a working login form varies per SEHA environment/deployment.
  The script (Step 6) tries the configured path first and automatically
  falls back to the other known one if the login form isn't found there, so
  you don't need to figure this out yourself ahead of time. It reports back
  whichever one actually worked (`LOGIN_PATH=...`) — persist that into
  `loginPath` so future runs for this project go straight to the right one
  instead of re-discovering it every time.
- `otp` → default to `"1234"` (the fixed value SEHA's dev/test environments
  accept for automated login — this only ever runs against dev/test SEHA
  environments in the first place, see "Scope" below).
- `envVarName` → default to `VITE_DEV_TOKEN`.
- `envFilePath` → default to `environments/.env.development.local`.
- `serviceName` → **no derivable default** — always ask the user the first
  time (e.g. "منصة الاحالات" for referral-frontend), then persist it as this
  project's default. Treat that persisted value as a default, not a fact
  that holds for every role in the project — the same SEHA environment can
  have several roles/accounts (see Step 4) whose menus don't all expose the
  same services (confirmed directly: a business/TPA account in one project's
  DEV environment simply didn't have the project's configured default
  service in its menu at all). If Step 6 fails specifically because the
  service wasn't found in the resolved role's menu, that means the default
  doesn't apply to *this* role — ask the user for the correct service name
  for that specific role rather than guessing a substitute yourself or
  treating it as a generic unexplained failure. Only overwrite the persisted
  project default if the user says this role's answer should become the new
  default; otherwise keep it role-scoped for this run.

Once confirmed/resolved, write the full config back to `docs/seha-auth/config.json`
so later runs don't ask or re-confirm again for the fields that are now known.
If a value later turns out to be wrong (e.g. the service was renamed in SEHA,
or an env var was renamed), the user can just tell you the correct value and
you update the file — don't be precious about it once
written.

---

## Step 3 — Resolve the users JSON file

Ask for the path if one hasn't already been given or found in the project
(no fixed on-disk convention to search for — this varies per project, always
confirm rather than guess a location). Once resolved, persist the path as
`usersJsonPath` in `docs/seha-auth/config.json` (same file as the rest of
Step 2's config, same "ask once, remember" treatment) so later runs don't
need to ask again.

**Never accept this file as a chat file attachment — always ask for it to be
pasted as inline plain text in the message instead, or read directly from a
path already on disk.** Confirmed firsthand (2026-08-05): a JSON file with
Arabic `label`/`accordionName`/`accountName` values, sent as a file
attachment, arrived with every non-ASCII character corrupted into mojibake.
Re-sending the identical file reproduced the identical corruption (ruling out
a one-off fluke), and the corruption was **not** mechanically reversible —
standard single- and double-pass Latin-1/cp1252 misread reversals all failed
with an invalid UTF-8 continuation byte, meaning actual data was lost, not
just shifted into a different representation. Pasting the same content as
plain text in a message, or pointing at a real file already saved on disk,
does not go through whatever lossy conversion file attachments go through
here — use one of those instead, every time, rather than re-attempting a fix
on attachment-sourced text.

Expected shape, one entry per account:

```json
[
  {
    "id": "cd9c0047-458a-4baf-9c63-08066c43a894",
    "label": "TPA (...)",
    "username": "7111111218",
    "password": "Pass@123",
    "accordionName": "حساب غير طبي خاص",
    "accountName": "موظف شركة التأمين الطرف الثالث - ...",
    "isBusiness": true
  }
]
```

`id` is the only field this skill treats as a stable identifier — everything
downstream (cache keys, disambiguation) keys off `id`, never off `label`
text, since labels can be edited/reworded across exports.

---

## Step 4 — Resolve which user profile to use

The caller specifies a role by short name (e.g. "TPA", "Facility", "Super
User"). Match against the JSON's `label` field:

- **Exactly one entry's `label` starts with (or clearly matches) that
  keyword** → use it directly, no need to ask.
- **Zero matches** → tell the user, show the actual `label` values present in
  the file, and ask them to point at the right one (the keyword they used
  may not match how this project's file labels that role).
- **More than one match** → **always ask**, every time, listing the full
  `label` (and `accountName`, since that's usually what actually
  distinguishes two same-role entries — different companies, different
  facilities). Never silently pick one and never remember a "default" for
  next time — this skill is generic across projects and a given short role
  can genuinely map to different real accounts, so guessing wrong means
  testing against the wrong org's data.

---

## Step 5 — Check the token cache before authenticating

Cache lives at `docs/seha-auth/cache.json` in the consuming project (separate
file from the config, deliberately — they're different kinds of data with
different lifetimes), gitignored, keyed by the JSON user's `id`:

```json
{
  "cd9c0047-458a-4baf-9c63-08066c43a894": {
    "token": "eyJ...",
    "obtainedAt": "2026-08-05T10:00:00.000Z",
    "expiresAt": "2026-08-05T12:00:00.000Z"
  }
}
```

This is a **same-session optimization, not durable storage** — SEHA tokens
are short-lived, so a cached entry from a prior day will almost always
already be expired by the time you'd reuse it. The point is purely to avoid
re-running the full browser flow multiple times for the same role within one
working session (e.g. several UI-validation checks in a row that all happen
to need "TPA").

Before running the script, check whether the selected user's `id` has a cache
entry whose `expiresAt` is still in the future (decode the cached JWT's `exp`
claim if `expiresAt` is missing rather than trusting a stale field, the same
way `src/shared/utils/jwt.ts`'s `isTokenExpired` already does in this repo).
If valid, **skip Step 6 entirely** and go straight to Step 7 with the cached
token.

If the cached token is later rejected by the server during actual use (a 401
or an explicit invalid-token response while testing), treat it as expired
regardless of what `expiresAt` says, drop the cache entry, and re-run Step 6.

---

## Step 6 — Run the flow

Only reached when there's no valid cached token. Invoke the bundled script,
always headless (never pass `--headed` unless a human is actively debugging
the flow itself, not as part of normal use):

```bash
node .claude/skills/seha-auth/scripts/get-token.mjs \
  --seha-base-url "<config.sehaBaseUrl>" \
  --login-path "<config.loginPath>" \
  --username "<user.username>" \
  --password "<user.password>" \
  --accordion-name "<user.accordionName>" \
  --account-name "<user.accountName>" \
  --service-name "<config.serviceName>" \
  --iframe-pattern "<config.iframeUrlPattern>" \
  --otp "<config.otp>" \
  --is-business    # only when user.isBusiness is true, omit otherwise
```

On success, the script prints two lines and exits 0:

- `TOKEN=<jwt>`
- `LOGIN_PATH=<path>` — whichever of the known login paths actually had the
  login form (see the `loginPath` note in Step 2). If it doesn't match
  `config.loginPath`, update the config with this value so the next run
  doesn't need to rediscover it.

On failure, it prints `ERROR=<message>` and exits 1. One cause gets special
handling, the rest don't:

- **`Service "<name>" not found in the services menu for this role.
  Available services: [...]`** — this specific message means the configured
  `serviceName` doesn't apply to the role that was just authenticated as
  (see the note on this in Step 2 — not every role/account in a project
  exposes the same services). Don't surface this as a raw failure and don't
  guess a substitute yourself: show the user the available-services list
  from the message and ask which one is actually correct for this role,
  then re-run Step 6 with the corrected `--service-name`. Only update the
  persisted `config.json` default if the user says this should become the
  project's new default.
- Everything else — surface the message to the user as-is; don't guess at a
  fix. Common causes: a selector changed on SEHA's side (the whole point of
  keeping selectors centralized in the script is that only one place needs
  updating), the account/accordion names in the JSON don't match what's
  actually on screen, or neither known login path had a login form at all
  (SEHA's login flow may have changed beyond these two variants).

On success, also decode the returned JWT's `exp` claim (base64url-decode the
middle segment, parse as JSON, `exp` is seconds since epoch) to compute
`expiresAt`, and write the cache entry for this user's `id`.

---

## Step 7 — Write the token into the target env file

Update `<config.envFilePath>` in the consuming project: set
`<config.envVarName>=<token>`, replacing the existing line for that variable
if present, appending it otherwise. Leave every other line in the file
untouched.

Writing to `environments/.env.development.local` will make Vite's dev server
auto-restart (it watches env files) — if a dev server is already running and
about to be used immediately after (e.g. by browser-check/run), wait for it
to come back up rather than navigating right away.

---

## Step 8 — Report

State plainly: which role/user was authenticated as, whether it came from
cache or a fresh run, and where the token was written. On failure, state
exactly what failed and why (from the script's `ERROR=` line), and don't
silently fall back to anything.

---

## Scope

This only ever produces tokens for **dev/test SEHA environments** — it exists
to satisfy a `import.meta.env.DEV`-only bypass in the consuming app (see
`src/shared/utils/auth.ts`'s `authenticateFromSeha`), which only activates in
development builds. It is not a path to obtaining staging/production tokens,
and the hardcoded dev-environment OTP (`"1234"`) reflects that — this skill
should never be pointed at a production SEHA environment.

## Gitignore

Unlike `docs/designs/`, `docs/stories/`, and `docs/browser-check/` (which are
wholly gitignored), only `docs/seha-auth/cache.json` gets ignored here —
add exactly that path (not the whole `docs/seha-auth/` folder) to the
consuming project's `.gitignore` the first time this skill is used there.
`config.json` and `users.json` are meant to be committed: they're small,
genuinely useful shared context (which SEHA environment, which service,
which test accounts exist), and don't change often. Tokens are the only
thing in this folder that's sensitive and constantly changing, so they're
the only thing excluded.

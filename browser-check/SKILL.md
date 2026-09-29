---
name: browser-check
description: Launch and drive this project's app in a real browser to verify a UI/frontend change — starting the dev server, reaching the changed page (asking the user for the auth method if one is needed, rather than assuming), interacting with the UI, and screenshotting the result. Use this whenever CLAUDE.md's Quality Gate requires testing a UI change in a browser, or whenever the default `run` skill's preferred tool (chromium-cli) isn't available.
---

# Browser Check Skill

> **Scope**: use this any time you've changed UI/frontend code and need to actually see it render and behave correctly — not just pass `tsc`/`eslint`/`vitest`. This satisfies CLAUDE.md's Quality Gate: *"For UI or frontend changes, start the dev server and use the feature in a browser before reporting the task as complete."*

This skill exists because the generic `run` skill's preferred driver (`chromium-cli`) isn't installed in this environment, so a Playwright-based fallback had to be worked out by hand once — this doc means the next agent doesn't have to redo that part.

**Everything about auth in this doc is deliberately generic.** Auth mechanisms vary wildly across projects — a login form, an env-configured dev token, SSO, a session cookie you already have, no auth at all locally — and guessing wrong wastes time or produces a false "it works" signal. Don't assume; ask (see "Handling auth" below). The one thing this repo happens to use today is recorded at the bottom purely as a cached, previously-learned answer — verify it's still true before trusting it, and treat it as an example of *one* possible answer, not the pattern.

---

## Quick recipe (TL;DR)

1. Find the dev command (`package.json` `scripts.dev`, or a project skill if one already covers launching this app) and start it in the background. Note the port — dev servers often fall back to the next free port if the default is taken.
2. In your **session scratchpad** (never the project directory — see "Don't touch project deps" below): `bun add -d playwright-core` (or `pnpm add -D playwright-core`).
3. Launch pointed at the **system-installed Chrome**, not Playwright's own bundled browser (see "Playwright's bundled browser isn't downloaded" below):
   ```js
   const browser = await chromium.launch({ channel: "chrome", args: ["--no-sandbox"] });
   ```
4. `page.goto()` the route you need. **If you land somewhere other than the app** (a login page, a 401/403, a blank/error state, an external redirect) — stop and go to "Handling auth" below. Don't guess your way past it.
5. Interact with the specific thing you changed, screenshot with `page.screenshot({ path: ... })` (see "Where the screenshot goes" below for the path), then **use the Read tool on the PNG** — don't just trust `textContent`. A blank frame is a failure to launch, not a pass.
6. Kill the dev server when done: `lsof -ti:<port> -sTCP:LISTEN | xargs -r kill`.

---

## Where the screenshot goes

The final screenshot always gets persisted to `docs/browser-check/<story-key-or-descriptive-name>/<surface-name>.png` in the project — never left only in the scratchpad. There's no case where you'd run this and not want to actually see the result yourself afterward, so this isn't conditional on being asked for.

- The scratchpad is still where the driver script itself and `playwright-core`'s `node_modules` live (see "Don't touch project deps" below) — only the final PNG leaves the scratchpad, not the automation code.
- Use a story key subfolder when one applies (a `sprint-planning` caller will tell you which); otherwise use a short descriptive name for the subfolder (the page/feature being checked) so a standalone run still lands somewhere identifiable.
- If `docs/browser-check/` doesn't exist yet in this project, create it, add `docs/browser-check/` to `.gitignore` (it's local reference material, same treatment as `docs/designs/`/`docs/stories/` if those already exist), and add a tracked `.gitkeep` so the folder itself persists.
- **Exactly one final image per surface** — if a screenshot reveals an issue that then gets fixed, delete the stale screenshot when re-capturing rather than accumulating a history of images for the same surface.

---

## Handling auth — always ask, never assume

The first time navigating to the target page doesn't land you on the actual app (redirected to a login screen, a 401, an external SSO domain, a blank shell, etc.), stop there. Do not:
- guess at a username/password combination,
- try to fabricate, mint, or reverse-engineer a token/session,
- silently give up and report success anyway,
- silently give up and report failure without asking whether there's a way through.

Instead, ask the user directly (a short `AskUserQuestion` or plain question both work — this is a case where pausing is clearly correct, not optional):
- What's the auth mechanism for local dev — a login form, a token from an env file, SSO, a browser session/cookie you already have, something else?
- What credentials or config values are actually needed to use it?
- Is there already a project skill (check `.claude/skills/`) or documented process for *obtaining* whatever's needed? Some projects separate "get a token" and "use a token" into two different skills — if so, the user may want to run the token-acquisition one first, or hand you the result of it.

Then adapt based on the answer — a few shapes this commonly takes:
- **Login form** (email/password, magic link, etc.): once the user gives you valid dev/test credentials (or confirms a seeded test user is fine to use), automate it with Playwright `fill`/`click` like any other form.
- **Env-configured dev token**: ask where it lives and how it's checked (e.g. a specific env var, a specific file). If it can expire, check that before relying on it, and say so plainly if it's missing or expired — don't spend more turns discovering that through a failed navigation.
- **Delegated to another skill**: if the user points you at a separate skill for obtaining a session/token, invoke that first, then come back and continue this recipe with whatever it produced.
- **No auth needed locally**: proceed directly — not every project gates its dev build behind auth.

Once you've learned the answer for a given project, it's fine to note it down (in this skill file, or a project-specific note) so it doesn't need re-asking every session — but only after the user has actually told you, and re-verify anything time-sensitive (like token expiry) before trusting a stale note. See the bottom of this doc for exactly that kind of cached note for this repo.

---

## Driver setup — challenges hit & their solutions (project-agnostic)

### `chromium-cli` isn't installed here

`which chromium-cli` → not found. The `run` skill's own fallback for this exact case: hand-roll a driver with `playwright-core`'s `chromium` module instead of `_electron`. That's what the recipe above does.

### Playwright's bundled browser isn't downloaded either

A bare `chromium.launch()` fails with `browserType.launch: Executable doesn't exist at .../chrome-headless-shell...`. Don't run `npx playwright install` to fix this — it downloads a browser binary over the network for a one-off check. Instead, reuse the Mac's already-installed Google Chrome:
```js
chromium.launch({ channel: "chrome", args: ["--no-sandbox"] })
```

### Don't touch project deps

`playwright-core` is **not** a dependency of this project (confirmed — no playwright/cypress/e2e tooling exists in `package.json`). Install it into your session's scratchpad directory, never into the project's `node_modules`/`package.json`/lockfile. This is a throwaway verification tool, not something the project should carry as a dependency.

### One console warning here is pre-existing library noise

MUI Autocomplete emits `Warning: A props object containing a "key" prop is being spread into JSX` on open, from `@mui/material` internals — unrelated to any app code. Don't treat this as a regression; only flag *new* errors that trace back to files you touched. (If this project's UI toolkit changes, re-derive which warnings are pre-existing noise vs. real — don't assume this specific one still applies.)

### MUI Autocomplete isn't a native `<select>` (this project's UI toolkit)

Dropdowns (`FormSelectInput`) are MUI Autocomplete-based here. `selectOption()` won't work on them. Click the input box to open the option list, then click the option's exact text:
```js
await page.getByPlaceholder("Choose the desired eligibility service").click();
await page.getByText("Hajj and Umrah", { exact: true }).click();
```
And placeholder strings live in the `placeholder` attribute, not as rendered text content — `getByText("Enter ID/Iqama Number")` times out; use `getByPlaceholder(...)` for inputs instead.

---

## Reusable script template

```js
import { chromium } from "playwright-core";

const browser = await chromium.launch({ channel: "chrome", args: ["--no-sandbox"] });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });

await page.goto("http://localhost:<port>/<route>", { waitUntil: "networkidle" });

// ...whatever gets you from the landing state to the thing you changed...
// ...interact with the specific thing you changed...

await page.screenshot({ path: "<scratchpad>/check.png", fullPage: true });
console.log("CONSOLE_ERRORS:", JSON.stringify(errors));

await browser.close();
```

Run with `node <script>.mjs` from inside your scratchpad directory (where `playwright-core` was installed).

---

## Cleanup

- Kill the dev server: `lsof -ti:<port> -sTCP:LISTEN | xargs -r kill`.
- Leave the scratchpad's `node_modules`/scripts where they are — the scratchpad is session-isolated and gets cleaned up on its own. Don't copy any of it into the project. Only the final screenshot leaves the scratchpad (into `docs/browser-check/`, per "Where the screenshot goes" above) — the driver script and `node_modules` never do.

---

## Cached note: this repo's current auth answer (learned 2026-08-04, verify before reuse)

This is a previously-learned answer to the "Handling auth" question above for *this specific repo* — not a rule, just what was true last time it was checked. Re-verify the time-sensitive parts (expiry) before relying on it; if anything's changed, ask again rather than assuming this is still accurate.

- The app is wrapped in `src/HOCs/ProtectPage.tsx`. With no valid token in the Redux store, it calls `authenticateFromSeha()` (`src/shared/utils/auth.ts`), which in dev redirects to `/?token=<VITE_DEV_TOKEN>` if that env var is set and unexpired — `ProtectPage` picks it up, stores it, and strips it from the URL. No form to fill.
- `vite.config.ts` sets `envDir: "./environments"`, so env vars aren't in a root `.env*` file — check `environments/.env.development.local` (gitignored, per-developer) for `VITE_DEV_TOKEN`, and `environments/.env.development` for `VITE_API_URL`.
- The token is a JWT with an `exp` claim and can expire — check it before trusting the auto-login will work. Per "Handling auth" above: check `.claude/skills/` first for a dedicated token-acquisition skill for this project before doing this by hand — if one exists and can't obtain what's needed (no matching role/user, not configured yet), it'll say so itself; don't fall back to forging or guessing a token either way.
- The token's `Permissions` claim is a comma-separated list of `PermissionType` enum values (`src/shared/models/User.model.ts`) that drive permission-gated UI branches (e.g. `isLimitedEligibility` in `src/hooks/app/useAppPermissions.ts`). Testing a different permission branch needs a genuinely different valid token from the user — not something to fabricate.
- `VITE_API_URL` points at a live dev/staging backend, not a local mock. Reading/rendering checks don't need a real form submit; be deliberate before triggering one.
- Reaching the actual feature usually means clicking through a services landing page (Arabic by default, with an "English" toggle in the header) rather than landing directly on the target form.

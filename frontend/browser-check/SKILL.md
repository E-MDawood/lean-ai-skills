---
name: browser-check
description: Drive this project's app in a real (headless) browser - start the dev server against mocks or the real backend, log in (via seha-auth or by asking the user, never by guessing), switch language, navigate, interact, capture screenshots, downloads, network requests and console errors. A capability skill - it doesn't decide what to test or judge results; frontend-testing and the sprint-planning quality gate use it for that. Use it directly for a quick "does this render" look at a UI change, or whenever the default `run` skill's preferred tool (chromium-cli) isn't available.
---

# Browser Check Skill

> **Scope: the browser, nothing more.** This skill knows how to start the app, get into it as a given role, and drive and observe a page. It does **not** own test scenarios, pass/fail judgments or test reports - those live in `frontend-testing`, which calls this skill. Use this skill directly only for a quick visual check of a change while building it.

It exists because the generic `run` skill's preferred driver (`chromium-cli`) isn't installed in this environment, so a Playwright-based driver had to be worked out once. This file means the next agent doesn't redo that.

---

## What callers can ask for

Other skills (and you, for a quick look) use this skill through these operations. Keep to them, so callers never have to re-explain the mechanics:

| Operation | What it does |
|---|---|
| **Start the app** | Start the dev server against **mocks** or the **real backend** (see "Starting the app"). |
| **Log in as a role** | Get a token for the role (`seha-auth` for SEHA-embedded apps, otherwise ask the user) and open the app with it. |
| **Set the language** | Switch the UI language (e.g. Arabic default, English toggle). |
| **Go to a page / act** | Navigate, click, fill, upload files, open modals, move through form steps. |
| **Observe** | Read texts, table rows, button lists, dialog content; capture network requests and responses (e.g. a request body); collect console errors. |
| **Capture** | Screenshot a surface; save a downloaded file. |
| **Stop the app** | Stop the dev server this skill started. |

---

## Driver setup

1. Work in your **session scratchpad**, never the project directory. Install the driver there, pinned:
   ```bash
   bun add playwright-core@1.48.2   # or: pnpm add -D playwright-core@1.48.2
   ```
   `playwright-core` is not a project dependency and must not become one. The scratchpad can be cleared between turns in a long session; if `node_modules/playwright-core` is gone, reinstall it before assuming anything else is broken.
2. Launch the **system Chrome**, not Playwright's bundled browser (it isn't downloaded, and `npx playwright install` would fetch it over the network for a one-off check):
   ```js
   const browser = await chromium.launch({ channel: "chrome", args: ["--no-sandbox"] });
   ```
3. Always headless. No visible browser window, ever.

### Script template

```js
import { chromium } from "playwright-core";

const browser = await chromium.launch({ channel: "chrome", args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (msg) => { if (msg.type() === "error") errors.push(msg.text()); });

// Network capture, when a caller needs a request body or response:
page.on("request", (r) => { if (r.method() === "PUT" && r.url().includes("/some-endpoint")) console.log(r.postDataJSON()); });

await page.goto("http://localhost:<port>/<route>", { waitUntil: "networkidle" });
// ...act...
await page.screenshot({ path: "<destination>.png" });
console.log("CONSOLE_ERRORS:", JSON.stringify(errors));
await browser.close();
```

Run with `node <script>.mjs` from the scratchpad.

---

## Starting the app

1. Find the dev command (`package.json` `scripts.dev`) and the mock toggle, if the project has one (this repo: `VITE_API_MOCK=true|false`, read in `src/main.tsx`). Pass the toggle on the command line rather than editing env files:
   ```bash
   VITE_API_MOCK=true bun run dev --port <port> --strictPort
   ```
   Prefer `bun` when available, else `pnpm`.
2. **Check the port before starting.** If something else is listening on it, identify it (`lsof -iTCP:<port> -sTCP:LISTEN`, then its command and working directory). If it's another project, **don't stop it** - tell the user and ask them to stop it or allow you to. Use `--strictPort` so a busy port fails loudly instead of silently moving to another port.
3. Confirm the page served is **this** app (e.g. check its `<title>`), not whatever else was on the port.
4. Stop only the server you started, when you're done: `lsof -ti:<port> -sTCP:LISTEN | xargs kill`.

## Logging in

- If navigating lands anywhere other than the app (a login page, 401/403, an SSO redirect, a blank shell), stop and resolve auth. Never guess credentials or fabricate a token.
- **Don't assume the auth method.** If the `seha-auth` skill is installed and the project is SEHA-embedded (see "Is this a SEHA project?" in `seha-auth`: e.g. `docs/seha-auth/config.json`, a SEHA env variable or host, or SEHA auth code), use `seha-auth` without asking and say which sign you found. Likewise if the user has already told you how to authenticate in this session. Otherwise, including when the repo looks like a SEHA project but `seha-auth` isn't installed, ask the user how local auth works (a login skill such as `seha-auth`, a login form with test credentials, an env token, an existing session) and follow their answer.
- **With `seha-auth`:** get a token for the role, then open the app with it. In this repo: `/?token=<token>` (picked up by `src/HOCs/ProtectPage.tsx`), which avoids rewriting the env file and restarting the dev server for each role.
- If several roles share one login, so that logging in as one invalidates the others (as on SEHA, see `seha-auth`), switch roles one at a time and log in again right before each.

## Where outputs go

- Screenshots and downloaded files are saved in the project at `docs/browser-check/<story-key-or-name>/` - never only in the scratchpad. Use the story key the caller gives you, or a short descriptive name.
- If `docs/browser-check/` doesn't exist yet, create it, add it to `.gitignore`, and add a tracked `.gitkeep`.
- **One final screenshot per surface and state.** When re-capturing after a fix, delete the stale image instead of keeping a history. Delete exploratory screenshots when you're done with them.
- After capturing, **look at the image** (Read the PNG). A blank or wrong frame is a failed capture, not a pass.

---

## Quirks of this project's UI toolkit

- MUI Autocomplete dropdowns aren't native `<select>`s: click the input, then click the option's text. Placeholders are attributes: use `getByPlaceholder(...)`, not `getByText(...)`.
- The UI is Arabic by default; the header has an "English" button to switch.
- Form fields render with `name` attributes (`contactInformation.ceo.firstName`, `nationalAddress`, …); prefer `input[name="..."]` selectors.
- Pre-existing console noise, not regressions: MUI Autocomplete's `A props object containing a "key" prop is being spread into JSX`, and `validateDOMNesting` warnings from `ExpiredTag`. Only report new errors that trace back to the change.

## Cached notes for this repo (verify before relying on them)

- **The real dev backend only accepts the app from `http://localhost:5173`** (CORS). Other ports load the app but every API call fails. If 5173 is taken, ask the user (see "Starting the app").
- With mocks on (`VITE_API_MOCK=true`), unmocked endpoints pass through to the real backend, so the same port rule applies.
- `vite.config.ts` reads env files from `environments/`. `VITE_API_URL` / `VITE_HPA_API_URL` point at the live dev backend.
- The app sends the UI language in a `culture` header on every request.

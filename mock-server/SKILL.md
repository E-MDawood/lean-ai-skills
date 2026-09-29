---
name: mock-server
description: "Use this skill when the user wants to set up a mock API server in a Vite + React (or similar) project, add new mock endpoints/handlers, or replicate the MSW-based mock setup used in other projects. Covers installing MSW, wiring it into the app entry point behind an env flag, and organizing handler files."
---

# Mock Server Skill (MSW)

> **Scope**: Use this when scaffolding mock API responses for local development — not for test-file mocking (jest/vitest module mocks, `vi.mock`) which is a separate concern.

---

## Overview

The mock setup uses **MSW (Mock Service Worker) v2** in **browser mode**. It intercepts real `fetch`/XHR calls at the network level — no separate server process or port — so the app's real API client code (RTK Query, axios, fetch, etc.) needs zero changes to work against mocks.

Key properties of this approach:

- **Opt-in via env var** — mocks are off by default and only activate when explicitly enabled, so they never leak into staging/production builds.
- **Lazy-loaded** — the mock module is dynamically `import()`-ed, so MSW code isn't bundled into the main chunk unless mocking is actually turned on.
- **Same response shape as the real API** — mock handlers return the exact same envelope (`{ code, message, data }`, pagination fields, etc.) the real backend uses, so consuming code never special-cases mock vs. real data.
- **Feature-based handler files** — one file per domain/feature, aggregated into a single handlers array.

---

## Setup Steps (new project)

### 1. Install MSW as a dev dependency

```bash
pnpm add -D msw
```

(Use the project's actual package manager — `npm`/`yarn`/`pnpm` — instead if `pnpm` isn't in use.)

### 2. Generate the service worker file

```bash
npx msw init public/ --save
```

This creates `public/mockServiceWorker.js` (generated file — never hand-edit it) and adds a config block to `package.json`:

```json
{
  "msw": {
    "workerDirectory": ["public"]
  }
}
```

Adjust `"public"` if the project's static asset directory has a different name.

### 3. Create the mocks directory structure

```
src/mocks/
├── browser.ts
└── handlers/
    ├── index.ts
    └── <feature>Handlers.ts
```

**`src/mocks/browser.ts`**

```ts
import { setupWorker } from "msw/browser";
import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);
```

**`src/mocks/handlers/index.ts`**

```ts
import { exampleHandlers } from "./exampleHandlers";

export const handlers = [...exampleHandlers];
```

**`src/mocks/handlers/exampleHandlers.ts`** — one file per feature/domain:

```ts
import { http, HttpResponse, delay } from "msw";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

const mockItems = [
    { id: 1, name: "First item" },
    { id: 2, name: "Second item" }
];

export const exampleHandlers = [
    // GET /items
    http.get(`${API_BASE}/items`, async () => {
        await delay(500);
        return HttpResponse.json({ code: 200, message: "Success", data: mockItems });
    }),

    // GET /items/:id
    http.get(`${API_BASE}/items/:id`, async ({ params }) => {
        await delay(300);
        const item = mockItems.find((i) => i.id === Number(params.id));
        return HttpResponse.json({ code: 200, message: "Success", data: item ?? null });
    }),

    // POST /items
    http.post(`${API_BASE}/items`, async ({ request }) => {
        await delay(800);
        const body = (await request.json()) as { name: string };
        return HttpResponse.json({
            code: 200,
            message: "Success",
            data: { id: Math.floor(Math.random() * 1000) + 10, name: body.name }
        });
    })
];
```

Match `{ code, message, data }` to whatever envelope shape the target project's real API actually uses — this is just the shape used in the reference project.

### 4. Add the env var toggle

Add to the relevant local/development env files (not staging/production/testing — mocks should be unavailable there by default):

```
VITE_ENABLE_MOCKS=false
```

Adjust the `VITE_` prefix to match the project's build tool if it isn't Vite (e.g. `NEXT_PUBLIC_`, `REACT_APP_`).

### 5. Wire mocking into the app entry point

In the file that bootstraps the React root (e.g. `src/main.tsx`):

```ts
async function enableMocking() {
    if (import.meta.env.VITE_ENABLE_MOCKS !== "true") return;

    const { worker } = await import("./mocks/browser");
    return worker.start({ onUnhandledRequest: "bypass" });
}

enableMocking().then(() => {
    ReactDOM.createRoot(document.getElementById("root")!).render(/* app tree */);
});
```

`onUnhandledRequest: "bypass"` lets any request without a matching handler fall through to the real network — important so partially-mocked features don't break unrelated requests.

### 6. Turn mocks on locally

Set `VITE_ENABLE_MOCKS=true` in the developer's local env file (e.g. `.env.development.local`, gitignored) and run the normal dev script. No dedicated npm/pnpm script is needed — it's just the env flag plus the normal dev server.

---

## Adding a New Mocked Endpoint (existing setup)

1. Find (or create) the feature's handler file under `src/mocks/handlers/`.
2. Add fixture data as plain local `const` arrays/objects at the top of the file — no factory library, no separate fixtures folder. Keep fixtures realistic enough to exercise loading/empty/filtered states.
3. Add the handler using `http.get/post/put/delete` from `"msw"`, prefixed with the same `API_BASE` constant used by other handlers in the file.
4. Simulate latency with `await delay(ms)` — use shorter delays (~300ms) for lookups/reads, longer (~800ms) for writes, so loading states are visible but not annoying.
5. Read dynamic input via `params` (path params), `new URL(request.url).searchParams` (query params), or `await request.json()` (body) as needed.
6. Return `HttpResponse.json(...)` matching the real API's response envelope exactly, including pagination fields if the real endpoint paginates.
7. If it's a new feature file, export its handlers array and spread it into `handlers/index.ts`.

---

## Conventions

- **One handler file per feature/domain**, not one giant file — mirrors how API slices are usually split by feature.
- **Fixtures live inline** in the handler file that uses them. Don't build a separate fixtures/factories layer unless the project already has one and reuse across many handler files is a real, current need.
- **Never hand-edit `mockServiceWorker.js`** — regenerate via `npx msw init public/ --save` if it needs updating (e.g. after an MSW major version bump).
- **Don't leave a half-migrated legacy mock layer** — if a project already has ad hoc mock data or a `queryFn`-swap pattern (temporarily replacing an RTK Query `query` with a `queryFn` returning fake data) predating MSW, prefer migrating those into proper MSW handlers rather than maintaining two mocking approaches side by side.
- **Mocks must default to off** in every env file except local development — never let `VITE_ENABLE_MOCKS=true` ship to a real environment.

---

## Checklist

- [ ] `msw` installed as a dev dependency
- [ ] `npx msw init public/ --save` run, `mockServiceWorker.js` present and untouched
- [ ] `src/mocks/browser.ts` + `src/mocks/handlers/index.ts` created
- [ ] At least one feature handler file created under `src/mocks/handlers/`
- [ ] Env var toggle (e.g. `VITE_ENABLE_MOCKS`) added to dev env files, defaulted to `false`
- [ ] Mock bootstrap wired into the app entry point behind the env flag, using a dynamic `import()`
- [ ] `onUnhandledRequest: "bypass"` set so unmocked requests still hit the real network
- [ ] Mock response envelopes match the real API's shape exactly
- [ ] Toggle verified: `VITE_ENABLE_MOCKS=true` locally shows mock data; unset/`false` hits the real backend

---
name: vitest
description: Use this skill for any change involving tests — new test files, editing existing ones, setting up vitest in a new project, or diagnosing test/pipeline failures. Covers vitest config, CI pipeline fixes, writing tests for components, hooks, utilities, and Redux, and running tests correctly.
---

# Vitest Skill

> **Scope**: Use this skill for **any change involving tests** — new test files, editing existing ones, setting up vitest in a new project, or diagnosing test/pipeline failures.

---

## Vitest Version Requirement

Use **vitest 3.0.0 or higher**. Do not install vitest 2.x or lower — the config and test patterns in this skill rely on vitest 3+ APIs.

The vitest version must be compatible with the project's vite version. The hard constraint only kicks in at vitest 4.1.0:

| vitest range | vite peer dep                    | Compatible with                                              |
| ------------ | -------------------------------- | ------------------------------------------------------------ |
| 3.x          | none                             | vite 4.x, 5.x                                                |
| 4.0.x        | none                             | vite 5.x, 6.x (no explicit constraint, but runtime may vary) |
| 4.1.x+       | `^6.0.0 \|\| ^7.0.0 \|\| ^8.0.0` | vite 6.x+ only                                               |

When setting up a new project, check the existing `vite` version in `package.json` first:

```bash
# For a project on vite 5.x — use vitest 3.x
pnpm add -D vitest@^3 @vitest/coverage-v8@^3

# For a project on vite 6.x+ — vitest 4.1.x+ is safe
pnpm add -D vitest@^4 @vitest/coverage-v8@^4
```

---

## Project Config Reference

The canonical config lives at `vitest.config.ts` in the project root:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
    test: {
        environment: "jsdom",
        globals: true,
        setupFiles: ["./src/test/setup.ts"],
        include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
        testTimeout: 30000,
        css: true,
        exclude: ["node_modules/**", "dist/**", ".git/**", "src/test/mocks/**"],
        coverage: {
            provider: "v8",
            reporter: ["text", "html", "lcov", "json-summary", "cobertura", "clover"],
            reportsDirectory: "./coverage",
            include: ["src/**/*.{ts,tsx}"],
            exclude: [
                "src/**/*.test.ts",
                "src/**/*.test.tsx",
                "src/test/**",
                "src/**/*.d.ts",
                "src/vite-env.d.ts",
                "src/main.tsx"
            ],
            thresholds: {
                lines: 40,
                functions: 40,
                statements: 40,
                branches: 50
            }
        }
    },
    resolve: {
        alias: [
            { find: "@", replacement: new URL("./src", import.meta.url).pathname },
            {
                find: /^.+\.(png|jpg|jpeg|gif|webp|mp4|mp3|wav|woff|woff2|ttf|eot|otf)$/,
                replacement: new URL("./src/test/mocks/fileMock.ts", import.meta.url).pathname
            }
        ]
    }
});
```

---

## Code Coverage & SonarQube

The GitLab CI pipeline uses **SonarQube as the authoritative coverage tool** — it is the source of truth for coverage results and thresholds, not the vitest terminal output. Vitest's job is to run the tests and produce coverage reports in a format SonarQube can consume; SonarQube then reads those reports and determines the final coverage numbers.

The project config already outputs the correct formats:

```ts
reporter: ["text", "html", "lcov", "json-summary", "cobertura", "clover"]
```

Both `lcov` (`coverage/lcov.info`) and `cobertura` (`coverage/cobertura-coverage.xml`) are formats SonarQube can ingest directly. Do not remove either of these reporters.

**Key rules:**
- When evaluating whether coverage passes or fails, defer to what SonarQube reports in the pipeline — not the vitest summary printed in the terminal.
- Do not set vitest `thresholds` to be the enforcement gate. Thresholds in `vitest.config.ts` are a local development aid only; the pipeline enforces coverage via SonarQube's quality gate.
- If a user reports a coverage failure in CI, check the SonarQube quality gate result — not the vitest exit code.
- Never remove `lcov` or `cobertura` from the reporters list, as doing so will break SonarQube's ability to read coverage data.

---

## Pipeline Fixes — Required Setup

These fixes are mandatory. Omitting any of them will cause CI failures.

### 1. Test Timeout

Set `testTimeout: 30000` in the config. The default (2000ms) is too short for tests that render async components or await RTK Query hooks. Without this, slow tests fail intermittently on CI.

### 2. CSS Processing

Set `css: true` in the config. Components import CSS/SCSS — without this, the test environment skips CSS processing and components that rely on class-based style assertions will behave incorrectly.

### 3. Test File Exclusions

Always include these `exclude` entries:

```ts
exclude: [
    "node_modules/**",
    "dist/**",
    ".git/**",
    "src/test/mocks/**" // prevents vitest from treating mock helpers as test files
];
```

The `src/test/mocks/**` exclusion is critical — without it, vitest scans mock helper files and fails trying to run them as tests.

### 4. Binary File Mock

Any component that imports images, fonts, or media will throw `TypeError: Unknown file extension` in jsdom. Fix this with a file stub and a resolve alias:

**`src/test/mocks/fileMock.ts`**:

```ts
export default "test-file-stub";
```

**In `vitest.config.ts` `resolve.alias`**:

```ts
{
    find: /^.+\.(png|jpg|jpeg|gif|webp|mp4|mp3|wav|woff|woff2|ttf|eot|otf)$/,
    replacement: new URL("./src/test/mocks/fileMock.ts", import.meta.url).pathname
}
```

### 5. No `@testing-library/react`

Never import `@testing-library/react` (or any of its companions like `@testing-library/jest-dom`, `@testing-library/user-event`) in setup files or test files. It is **not installed** and adding it breaks the CI pipeline. Use `react-dom/client` + `act` directly for component/hook tests — see the "Testing React components" section below for the canonical pattern.

### 6. Legacy Peer Dependencies (`.npmrc`)

Create `.npmrc` in the project root with:

```
legacy-peer-deps=true
```

This prevents `npm install` from hard-failing on mismatched peer version ranges across older packages. Without it, CI installs fail on dependency trees that have minor version conflicts.

---

## Test Setup File

`src/test/setup.ts` runs before every test file. Keep it minimal — only global stubs that apply to every test:

```ts
import { vi } from "vitest";

vi.stubEnv("TZ", "UTC");
```

---

## File & Naming Conventions

-   Test files live **next to the file under test**, in the same directory.
-   Use `.test.ts` for tests with no JSX, `.test.tsx` for tests that use JSX syntax directly.
-   Both are picked up automatically — the `include` pattern covers `src/**/*.test.ts` and `src/**/*.test.tsx`.

---

## Writing Tests

### Imports

Always import test utilities explicitly from `vitest`:

```ts
import { describe, it, expect, vi, beforeAll, beforeEach, afterEach } from "vitest";
```

`globals: true` is set in the config, so these are available globally — but explicit imports are preferred for clarity.

### General structure

```ts
import { describe, it, expect, vi } from "vitest";
import { myFunction } from "./myModule";

describe("myFunction", () => {
    it("returns expected value for valid input", () => {
        expect(myFunction("input")).toBe("expected");
    });

    it("handles edge case", () => {
        expect(myFunction("")).toBeNull();
    });
});
```

### Mocking modules

Use `vi.mock` at the top of the file, before imports of the module under test:

```ts
import { describe, it, expect, vi } from "vitest";

vi.mock("@/shared/utils/auth", () => ({
    authenticateFromSeha: vi.fn()
}));

import { someFunction } from "./myModule";
```

Use `vi.hoisted` when mock factory values need to be referenced before `vi.mock` runs:

```ts
const { myMock } = vi.hoisted(() => ({
    myMock: vi.fn()
}));

vi.mock("@/some/module", () => ({
    default: () => myMock()
}));
```

### Mocking SVG / icon components

jsdom cannot render SVG React components (imported via `?react` suffix). Stub them explicitly per test file:

```ts
vi.mock("@/assets/icons/IconExample.svg?react", () => ({
    default: () => null
}));
```

Or, for tests that need multiple icon stubs, import the shared stub map from `src/test/mocks/svgReactIconStubs.ts`:

```ts
import { svgReactIconStubs } from "@/test/mocks/svgReactIconStubs";

vi.mock("@/assets/icons/IconExample.svg?react", () => ({
    default: svgReactIconStubs.IconExample
}));
```

### Testing React components (without React Testing Library)

Use `react-dom/client` + `act` directly (RTL is not installed):

```ts
import { act, createElement } from "react";
import { createRoot } from "react-dom/client";
import { beforeAll, describe, it, expect } from "vitest";

beforeAll(() => {
    (globalThis as unknown as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT =
        true;
});

describe("MyComponent (smoke)", () => {
    it("renders without throwing", () => {
        const container = document.createElement("div");
        const root = createRoot(container);

        act(() => {
            root.render(createElement(MyComponent, { prop: "value" }));
        });

        expect(container.querySelector('[data-testid="my-element"]')).not.toBeNull();
    });
});
```

Always set `IS_REACT_ACT_ENVIRONMENT = true` in `beforeAll` when using `createRoot` — this suppresses act() warnings in jsdom.

### Testing with Redux store

```ts
import { configureStore } from "@reduxjs/toolkit";
import { Provider } from "react-redux";
import { authSlice } from "@/store/authSlice";

function makeStore(token = "") {
    return configureStore({
        reducer: { auth: authSlice.reducer },
        preloadedState: { auth: { token } }
    });
}

act(() => {
    root.render(
        createElement(Provider, { store: makeStore("my-token") }, createElement(MyComponent))
    );
});
```

### Testing hooks

Use a minimal functional component wrapper to invoke hooks under `act`:

```ts
import { act, createElement, useState } from "react";
import { createRoot } from "react-dom/client";

it("hook returns expected value", () => {
    let result: ReturnType<typeof useMyHook>;

    const Wrapper = () => {
        result = useMyHook();
        return null;
    };

    const container = document.createElement("div");
    act(() => {
        createRoot(container).render(createElement(Wrapper));
    });

    expect(result!.someValue).toBe("expected");
});
```

### Testing pure utilities

No DOM setup needed:

```ts
import { describe, it, expect } from "vitest";
import { formatDate, parseAmount } from "./formatters";

describe("formatDate", () => {
    it("formats ISO string to DD/MM/YYYY", () => {
        expect(formatDate("2024-01-15")).toBe("15/01/2024");
    });
});
```

---

## Running Tests

```bash
# Run affected files only (preferred after any change)
pnpm test src/path/to/file.test.ts src/path/to/other.test.ts

# Run full suite with coverage
pnpm test

# Watch mode during development
pnpm test:watch
```

Always run `pnpm test <affected files>` after any change before marking work complete. Only run the full suite when specifically requested.

---

## Checklist for New Tests

-   [ ] Test file is in the same directory as the file under test
-   [ ] File is named `<filename>.test.ts` (no JSX) or `<filename>.test.tsx` (JSX syntax)
-   [ ] Vitest imports are explicit (`from "vitest"`)
-   [ ] `vi.mock` calls are before the import of the module under test
-   [ ] SVG/icon imports are stubbed
-   [ ] Binary asset imports are handled by the `fileMock` alias (no extra setup needed)
-   [ ] React tests set `IS_REACT_ACT_ENVIRONMENT = true` in `beforeAll`
-   [ ] Tests pass locally with `pnpm test <file>` before committing
-   [ ] No imports from `@testing-library/*` anywhere in the test or setup files

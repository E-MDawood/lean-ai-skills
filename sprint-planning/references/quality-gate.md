# Phase 8 reference — Quality gate

Run this before considering a story, or the sprint, done — not just at the very end. It's cheapest to catch issues right after the task(s) that introduced them, not after the whole sprint is implemented.

Skills named below (`fallow`, `vitest`, `review`, `security-review`) exist in this repo but may not exist in every repo this skill runs in. If one isn't available where you're currently working, don't skip the underlying check — run the closest available equivalent manually (that repo's own test runner, its own linter, a manual review pass) instead.

## Checks

- **Focused tests** on the files a task actually touched (`pnpm exec vitest run <file1> <file2>` on the frontend; the backend repo's equivalent test runner). Run the full suite only when asked or when the change has broad impact.
- **Lint** (`pnpm lint` on the frontend).
- **Type check / build** when the change touches shared types, API payloads, routing, or otherwise broad app behavior.
- **Localization**: every new or changed piece of user-facing text has a key in both `en` and `ar` translation files (frontend) — never one without the other.
- **State coverage**: verify required vs. optional, read-only vs. editable, loading, and error states all match what the plan specified — not just the happy path.
- **Self-review pass**: use the `fallow` skill after any change that touches multiple files or is substantial enough to warrant it (refactors, shared utility changes, workflow/state changes, repeated-logic extraction, large multi-file feature edits). Skip it for small, clearly isolated changes where the extra pass wouldn't add value. Scope it to the current task's changed files, not the whole project. When it surfaces something in scope, fix it and rerun the relevant check to confirm — treat it as a self-correction loop, not a one-shot report. Don't use its findings as an excuse to touch unrelated old code.
- **Code review**: use the `review` skill for a broader pass, or `security-review` specifically when the change touches auth, permissions, external input, or anything else security-sensitive.
- **Repo-specific gotchas worth double-checking** (frontend): pnpm, not npm or yarn; environment variables must be prefixed `VITE_`; routing is hash-based (`createHashRouter`); Husky runs a security audit on pre-commit, don't bypass it.

## Plan-fidelity check (distinct from the checks above)

The checks above verify the code is *good* — well-tested, lint-clean, not duplicated, not insecure. This one verifies something different: that the code actually *matches what the plan specified*. Code can pass every check above and still have drifted from intent — a field that should be conditional got made always-required, a component the plan said to reuse got rebuilt from scratch instead, a rule scoped to one case in the plan got applied everywhere in the implementation.

Run this the same way as the Phase 4 plan review: use the `Agent` tool in a **fresh context** — a subagent with no memory of having written the code, given the actual diff/changed files for the story and that story's section of the plan (`stories-plan.md`/`<feature>-plan.md`). Ask it to adversarially compare the two, not confirm they match, and flag:

- Anything the plan specified that the implementation didn't actually do (a requiredness rule, a conditional, a validation, a specific value).
- Anywhere the plan said reuse or extend an existing component/pattern and the implementation built something new instead.
- Any deviation from the plan at all — flag it explicitly, then confirm with the user whether it was an intentional, justified change or an accidental drift, rather than silently deciding either way.

Run this per story (or per task group) before considering it done, alongside the checks above, not instead of them.

## UI validation (frontend only)

Only applies when the project is frontend (Step 0 detection) and only to tasks/stories with an actual UI surface — skip it for pure type/model/backend-adjacent changes. Unlike the plan-fidelity check above, this runs in the **same context** that implemented the UI, not a fresh subagent: the point is to confirm the implementation matches the intention the implementing agent already had in mind (from a design, or imagined if there wasn't one), which a fresh reviewer couldn't judge without first being told that intention anyway.

For each distinct UI surface (a page, a modal, a flow-state) a story touches:

1. **Check whether the backend endpoint(s) it needs are actually ready** — try the real call from the running app first.
   - Ready → proceed straight to capture against the real API.
   - Not ready → check whether the current repo has a mock-server-style skill (this repo: `mock-server`). If yes, use it to add or extend just enough of a mock handler to exercise the needed states (loading/empty/populated/error), enable it, then proceed against the mock.
   - No mock-capable skill available in this repo → **stop and tell the user explicitly**: name the endpoint, state that UI validation for it can't proceed without a mock skill, and ask them to either add one or explicitly say to skip this specific check. Never skip silently. If skipped, note it as an explicit known gap (e.g. a line in `tasks.md` noting this surface wasn't visually validated and why) rather than just dropping it.
2. **Check whether reaching the surface requires authentication, or a specific role.** Never hardcode, guess, or invent a login method, test credentials, an auth-bypass flag, or a way to switch roles — auth setup varies per project and is the user's decision, not something to work around unilaterally. If the agent doesn't already have a working way to authenticate as whatever role the surface needs, **stop and ask the user directly**: which credentials/account to use, how to log in, or how to switch to the required role. Same rule as the mock-skill gap above: never silently skip past this or improvise a workaround. If the user has no answer and says to skip, note it as an explicit known gap the same way.
   - This is exactly the situation `browser-check` (see step 3 below) already asks about natively — if it's the one doing the driving, its own auth prompt covers this. This step matters most when `run` is doing the driving instead and has no such awareness built in.
   - For a project whose app is embedded inside SEHA specifically, the `seha-auth` skill is the concrete answer to that auth question: it gets a real dev/test token headlessly and writes it into the project's env file. Use it (or point the user at it) instead of improvising a SEHA workaround from scratch.
3. **Launch and drive the app headless** — delegate to the `run` skill first, it already knows how to do this per project type. If `run`'s preferred tool isn't available or it fails, fall back to the `browser-check` skill instead of improvising a Playwright/Puppeteer setup by hand — it's built for exactly this fallback role and already knows to ask about the auth method rather than assume one. No visible browser window, ever, regardless of which of the two ends up driving.
4. **Capture one screenshot** of the surface in its expected state(s), and tell whichever tool is driving to save it under `docs/browser-check/<STORY-KEY>/<surface-name>.png` — `browser-check` knows this destination and will target it directly when asked. If the tool doing the driving doesn't support a destination argument, take whatever it produced and move it there yourself; don't leave it wherever the tool's own default is.
5. **Compare against the intended look**:
   - A design exists (`docs/designs/`, `docs/stories/<key>/`) → compare against it directly: layout, content, behavior.
   - No design exists → compare against the look the implementation was written to produce: nothing visually broken (overlap, cut-off text, misalignment), all relevant states rendering correctly, labels/text correct in both languages including RTL layout, and logical correctness (conditional fields/buttons actually behaving as specified, not just present).
6. **End with exactly one screenshot per surface** at `docs/browser-check/<STORY-KEY>/<surface-name>.png`. If a screenshot reveals an issue that gets fixed, delete the stale screenshot when re-capturing — never leave more than one image for the same surface.
7. **Report findings** — what was checked, what passed, what didn't and got fixed, what was skipped and why — rather than silently passing or failing.

## After the gate

Once every task in `tasks.md` for the current story (or the whole sprint) is checked and has passed this gate, the sprint-planning cycle for that scope is complete. If new work surfaces after this point that wasn't in the original stories, treat it as a new pass through this same skill rather than quietly extending the current one.

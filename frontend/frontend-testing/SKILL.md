---
name: frontend-testing
description: Test a frontend batch or story end to end, against MSW mocks during implementation and against the real deployed backend once it ships, and produce a test report - what works, frontend issues, backend issues, and blocked scenarios. Runs the scenarios from the batch's plan for each role and language, through the browser-check skill (driving the app), browser-check's login (which uses seha-auth when the repo shows it's a SEHA project, and otherwise asks the user how to authenticate) to log in as each role and db-test-setup (when a scenario needs data that doesn't exist, or writes data that must be restored). Use it in the sprint-planning quality gate (Phase 8), after a backend deployment or fix round, or when the user asks to "test this end to end", "retest after the backend deployed" or "check it against the real backend".
---

# Frontend Testing Skill

> **What it does:** runs the planned test scenarios for a story or batch in a real browser, checks what the UI shows and what it sends, and reports the results in four lists. It reports backend issues; it never changes backend code.
>
> **What it uses:** `browser-check` to drive the app (it never re-implements the browser mechanics), `browser-check`'s "Log in as a role" to get in as each role (it uses `seha-auth` when the repo shows it's a SEHA project, and otherwise asks the user how to authenticate), and `db-test-setup` when a scenario needs data the environment doesn't have, or writes data that must be restored afterwards.

---

## Step 1 — Gather the inputs

1. **Scenarios:** take them from the plan, not from memory or imagination:
   - the batch's `stories-plan.md` (its **Test Plan**, especially the "Browser check" list);
   - the batch's `tasks.md` (the browser-check task);
   - for a retest, the open rows in the batch's `api-changes-inconsistencies.md`.

   If a scenario in the plan is unclear, ask rather than guess.
2. **Contract:** the batch's contract file (`frontend-to-backend-api-changes.md` or `backend-to-frontend-api-contract.md`). It tells you what the backend should send, so you can tell a frontend issue from a backend one.
3. **Mode:**
   - **Mocks** during implementation, when the backend hasn't deployed yet.
   - **Real backend** once it has. Check first that the endpoints actually respond on the dev backend; if they don't, say so and fall back to mocks, marking real-backend scenarios as not yet testable.
4. **Roles and languages:** list each role the scenarios need, and test in both languages (Arabic and English) unless a scenario is language-independent.

## Step 2 — Prepare

1. Start the app through `browser-check`, in the chosen mode.
2. Plan the roles: group the scenarios by role. If several roles share one login, so that logging in as one invalidates the others (as on SEHA, see `seha-auth`), run them one after another, logging in again right before each.
3. For each scenario, check that the environment has the data it needs (a request in the right state, the right sector, the right role assignment).
   - **Mocks:** if a mock scenario lacks the data, extend the mock handlers (dev tooling only).
   - **Real backend:** if the data doesn't exist and can't be created through the app, use `db-test-setup` to set it up and restore it afterwards.
4. **Real backend:** for each scenario that writes data (a reassign, a submit, a workflow step), use `db-test-setup` in restore-only mode, so it snapshots the rows the scenario will write before it runs and restores them afterwards, even when no setup is needed.
5. If the user declines to give a connection string, keep testing everything else. Mark each scenario that needed `db-test-setup` (for setup or for restore) **blocked - needs data**, and don't run it.

## Step 3 — Run the scenarios

For each scenario, role and language:

1. Drive the app to the surface through `browser-check`.
2. Check what the plan says should happen:
   - **What the UI shows:** texts, labels, buttons present or absent, values, empty/error/loading states, RTL and LTR layout.
   - **What the app sends:** capture the request when the scenario is about the payload (e.g. a request body field), and compare it with the contract.
   - **What comes back:** when the UI looks wrong, call the endpoint directly with the role's token to see whether the backend sent the wrong data or the frontend rendered it wrong.
   - **Side effects:** when the scenario writes data, confirm the result through the app or the API (and read-only through `db-test-setup`'s connection if one was given).
3. Capture one screenshot per surface and state, in the story's `docs/browser-check/` folder. Look at every screenshot before calling it a pass.
4. Note console errors that trace back to the change; ignore known pre-existing noise (`browser-check` lists it).

A scenario only passes when you saw it work. If it couldn't be run, it's blocked, not passed.

## Step 4 — Classify every finding

| Finding | Goes in |
|---|---|
| Works as planned | **Tested and working** |
| The frontend does the wrong thing with correct backend data (wrong label, missing state, wrong payload, broken layout) | **Frontend issues** - fix the clear ones right away (see "Fixing frontend issues" below) |
| The backend sends or does something different from the contract (wrong value, wrong shape, missing translation, wrong error) | **Backend issues** - report only, never change backend code from a frontend repo |
| Couldn't be run | **Blocked**, with the reason: *needs data* (the scenario needs data changed in the database, to set it up or to restore what it writes, and no database access was given), *unsafe to proceed* (`db-test-setup` stopped, e.g. the environment couldn't be confirmed as non-production or no safe restore was possible), or *backend bug* (a backend issue that stops the scenario from being reached) |

### Fixing frontend issues

Fix an issue on your own only when it's **clear**: the plan, the contract or the design says one thing, the code does another, and nothing suggests the difference is intended (a wrong label, a missing loading state, a wrong field in a payload, a broken RTL layout).

For each clear issue:
1. Fix it, following the repo's conventions.
2. Add or update the tests for the changed files, and run them.
3. Re-run the affected scenarios, and repeat until they pass.

**When in doubt, don't fix it: report it and ask the user first.** That covers anything that would change a business rule or the plan, code that looks deliberate (a comment, a decision in `analysis-notes.md`, a recent commit), cases where the plan and the design disagree, and fixes that would reach beyond the scope of the batch.

## Step 5 — Restore and clean up

1. If `db-test-setup` changed data, have it restore and verify everything before reporting.
2. Stop the dev server you started.
3. Delete exploratory screenshots; keep one final screenshot per surface and state.

## Step 6 — Report

Write the report in this order:

1. **Tested and working** - a table: *Check* | *Result*, one row per scenario (with role and language where they matter).
2. **Frontend issues** - each with what happened, what the plan says should happen, and where (file or screen). For each one, say how it was fixed and that its scenarios now pass, or that it's waiting for the user's confirmation and why.
3. **Backend issues** - each with the endpoint, what the contract says, what the API does, and an example request/response.
4. **Blocked scenarios** - each with the reason: *needs data*, *unsafe to proceed*, or *backend bug* (naming the bug).

Then two short sections:

- **Data changed and restored** - from `db-test-setup`'s report (it reports only on the data; this skill owns pass or fail), including any difference left after the restore. Say "none" if no data was changed.
- **Screenshots and files** - where they are.

Also update the planning docs:
- Add the backend issues as open rows in the batch's `api-changes-inconsistencies.md`, and remove rows that the test confirmed fixed (record the confirmation in `analysis-notes.md`).
- Tick the browser-check task in the batch's `tasks.md` when every scenario passed, or note which ones are still blocked and why.

## Re-testing

After each backend fix round, re-run **only** the scenarios tied to the fixed rows, plus a quick pass over what already worked to catch regressions. Report against the previous results: what's now fixed, what's still open, and anything new.

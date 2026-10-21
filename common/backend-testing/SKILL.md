---
name: backend-testing
description: Test a backend's API endpoints directly against their contract - role access, validation, happy path, response shape, error envelope, both languages and side effects - and report what works and what doesn't. Two modes, picked by the repo it runs in. In a backend repo it tests the API running locally before handover, fixes what it finds and re-tests in the same loop. In a frontend repo it tests the already deployed dev backend and only reports backend issues, never changing backend code. Asks the user how to authenticate each role (using seha-auth directly when the repo shows it's a SEHA project), and uses db-test-setup when a case needs data that doesn't exist or writes data that must be restored. Use it in the sprint-planning quality gate (Phase 8), after a backend deployment or fix round, or when asked to "test the API", "check the endpoints" or "verify the backend against the contract".
---

# Backend Testing Skill

> **Purpose:** catch API problems early, before the frontend's end-to-end testing has to find them through the UI. It's the backend's counterpart to `frontend-testing`.

---

## Step 0 — Pick the mode

Detect the repo type the same way `sprint-planning` does (Step 0 there):

| Repo | Mode | Target | On a problem |
|---|---|---|---|
| **Backend** (`*.csproj` / `*.sln` or equivalent) | **Self-review** | The API **running locally** | Fix it, re-run the affected cases, repeat until clean |
| **Frontend** | **Contract check** | The **deployed dev backend** (the only one you have access to) | Report it as a backend issue; **never** edit backend code |

In contract-check mode you may read the backend's source (if it's reachable on disk) to understand a failure or check a case you can't trigger, but every finding still goes into the report, not into a fix.

## Step 1 — Gather the inputs

1. **The contract:** whichever side wrote it - `backend-to-frontend-api-contract.md` / `backend-to-frontend-api-changes.md`, or `frontend-to-backend-api-changes.md` - plus the open rows of `api-changes-inconsistencies.md` for a retest. Don't depend on frontend code: the contract is the source of truth for what the API should do.
2. **The endpoints in scope:** the ones the batch or story adds or changes. List them with method and path.
3. **Base URL:** the local API (self-review) or the dev backend (contract check).
4. **Roles and auth:** which roles may call each endpoint, and which may not. Don't assume how the project authenticates:
   - **Already known:** if the `seha-auth` skill is installed and the project is SEHA-embedded (see "Is this a SEHA project?" in `seha-auth`: e.g. `docs/seha-auth/config.json`, a SEHA env variable or host, or SEHA auth code), use `seha-auth` without asking and say which sign you found. Likewise if the user has already told you how to authenticate in this session. `seha-auth` returns the token for an `Authorization: Bearer` header; no env file.
   - **Otherwise, ask the user**, including when the repo looks like a SEHA project but `seha-auth` isn't installed, how to get a token or session for each role, e.g. a login skill such as `seha-auth`, a login endpoint with test credentials, a token they give you, an API key, or a cookie session. Then follow their answer.
   - Never guess credentials or fabricate a token.

   If several roles share one login, so that logging in as one invalidates the others, run those roles one after another, with a fresh token before each.

## Step 2 — Build the cases

For each endpoint, cover:

| Area | Cases |
|---|---|
| **Access** | Each allowed role succeeds. Each disallowed role gets the contract's status (400/401/403). No token gets 401. A caller outside the record's scope (another organisation, region or sector) is refused as the contract says. |
| **Validation** | Missing required fields, wrong types, out-of-range values, unknown enum values, too-long strings. Each gets the contract's error status and message. |
| **Happy path** | The main success case(s), with realistic data. |
| **Response shape** | Field names, types, nullability, enums as numbers or strings, date format, ordering, empty-list behaviour - all exactly as in the contract. |
| **Error envelope** | Errors use the standard envelope (e.g. `{ code, message, data }`) and a readable message, not an internal key. |
| **Language** | Localised text (labels, messages) correct in both languages, using whichever header or parameter the backend reads for the language (e.g. `Accept-Language`, or a custom header such as `culture`). Skip this area if the API isn't localised. |
| **Side effects** | What the call should change in the data (status, stage, related rows, log rows) really changed, and nothing else did. Check it through the API, or read-only through `db-test-setup`'s connection if the user gave one. |
| **Edge cases** | Whatever the contract calls out (e.g. an empty list meaning "nothing changed", a field ignored in some states, idempotency of a repeated call). |

If a case needs data that doesn't exist, use `db-test-setup` to set it up; if a case writes data, use it in restore-only mode so the rows are snapshotted before the call and restored after. If the user declines to give a connection string, keep testing the other cases and mark each of these **blocked - needs data**; if `db-test-setup` stops for safety, **blocked - unsafe to proceed**.

## Step 3 — Run them

- Call the endpoints directly (`curl`, or a short script in the scratchpad with Playwright's `request` context or `fetch`). Log the request and response of every failing case.
- Keep calls that change data to the minimum the case needs, and restore through `db-test-setup` afterwards.
- **Self-review mode:** when a case fails and the issue is **clear** (the contract says one thing, the code does another, and nothing suggests the difference is intended), fix the code, run the backend's own tests for the touched area, and re-run the failed case plus the endpoint's other cases. Repeat until clean. **When in doubt, don't fix it: report it and ask the user first.** That covers anything that would change a business rule or the contract, code that looks deliberate (a comment, a recorded decision, a recent commit), cases where the contract and the requirements disagree, and fixes that would reach beyond the scope of the story.
- **Contract-check mode:** when a case fails, record it with the request and response, and move on.

## Step 4 — Report

Use the same four lists as `frontend-testing`:

1. **Tested and working** - a table: *Endpoint / case* | *Result*.
2. **Frontend issues** - only in contract-check mode, if the contract itself is wrong or ambiguous on the frontend's side (otherwise "none").
3. **Backend issues** - endpoint, case, what the contract says, what the API does, and the example request/response. In self-review mode, list what was found and how it was fixed, and each issue left waiting for the user's confirmation, with why.
4. **Blocked cases** - each with the reason: *needs data*, *unsafe to proceed* (`db-test-setup` stopped), or *backend bug*.

Then:
- **Data changed and restored** - from `db-test-setup`'s report (data only; this skill owns the case results), or "none".
- **Contract updates** - in contract-check mode, add the backend issues as open rows in the batch's `api-changes-inconsistencies.md`; in self-review mode, update the backend's contract file if the fix changed behaviour the frontend relies on, and say so.

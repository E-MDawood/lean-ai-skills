# Phase 5 reference — API contract files

Only relevant when the sprint involves a change to the API contract between frontend and backend. Skip this phase entirely otherwise.

## Determine the contract mode first

Backend and frontend don't always plan in lockstep — sometimes backend has already built (or fully specified via Swagger) the endpoints this sprint needs before frontend planning even starts. That changes how this phase works:

- **Swagger-is-source-of-truth mode**: the relevant endpoints already exist and `docs/api/swagger.json` reflects them. Skip the propose-and-reconcile cycle for anything Swagger already covers — read those endpoints straight from Swagger and use them as-is in the dev plan (Phase 4), no contract file needed for them. Only write a contract-change file, scoped to the specific gap, when a story needs something Swagger genuinely doesn't support yet.
- **Proposal mode** (the default described below): backend hasn't built this yet, or Swagger doesn't reflect this sprint's planned work. Write a full contract-change file proposing what's needed, and reconcile with the other side's own proposal via `api-changes-inconsistencies.md`.

**How to decide**: if the user's prompt already states which applies ("backend already built this," "Swagger's up to date for this sprint," or conversely "backend hasn't started yet"), go with that. If it's not stated, ask directly — don't assume either way, since guessing wrong means redoing this phase's output entirely. This can vary per story within the same sprint (some endpoints already shipped, others not); when it's unclear for a specific story, check `docs/api/swagger.json` for that story's endpoint first, and if what's there might be a stale draft rather than the real, final contract, confirm with the user rather than trusting it blindly.

## Which file to write

Each side writes the contract changes *it* requires from the other side — never write the other side's file for them:

- **Frontend** writes `frontend-to-backend-api-changes.md` — the API changes the frontend needs the backend to implement.
- **Backend** writes `backend-to-frontend-api-changes.md` — the API changes the backend is exposing to the frontend.

Both sides then exchange files and compare them to produce `api-changes-inconsistencies.md`.

## Structure — contract change file

```
# Sprint <number> API Contract Changes

## Summary

## Contract Changes
| Story | Required contract changes |
|---|---|

## Proposed Shared Types      (when enums/types are involved)
```

- **One row per story that actually needs this file.** In proposal mode that's every contract-touching story; in Swagger-is-source-of-truth mode it's only the stories with a genuine gap. Multiple required changes for the same story go as concise bullet sentences inside that story's single cell, not as extra rows.
- **Explicit endpoint paths always** — `POST /reports`, `PUT /reports/{id}`, `GET /reports/{id}`. Never a generic phrase like "create/update endpoint."
- **Concrete proposals, not open questions** — write the actual proposed enum values, payload fields, response fields, and endpoint paths. In proposal mode, if a contract isn't in `docs/api/swagger.json` yet, propose it anyway with the same concreteness. In Swagger-is-source-of-truth mode, only propose the delta beyond what Swagger already defines — don't restate what it already covers.
- **No placeholders** like `TBD_ID` in the first pass. State the proposal as if it were final; refine later if the other side pushes back.
- **Don't invent the other side's internals.** Propose only the integration contract your own side requires — not how the other side should implement it, unless they've explicitly asked for that.
- **Keep concerns separate**: implementation details stay in `stories-plan.md`/`<feature>-plan.md`; this file is the shared contract only.

In **proposal mode**, `docs/api/swagger.json` is a planning reference, not a strict source of truth — both sides typically plan in parallel, so it may lag. Keep using it for context but document the concrete proposal here regardless of whether Swagger reflects it yet. In **Swagger-is-source-of-truth mode**, Swagger *is* the strict source of truth for whatever it already covers — this file exists only to capture what it doesn't.

## Structure — inconsistencies file

```
# Sprint <number> API Contract Inconsistencies

## Summary

## Inconsistencies
| Story | Area | Frontend proposal | Backend proposal | Resolution |
|---|---|---|---|---|

## Resolved Decisions
```

Use this file only for actual mismatches or unresolved integration questions between the two sides' proposals — not for restating agreement. Once an inconsistency is resolved, update the source contract files (and the dev plan, if it assumed the old contract) to match, and move the row's outcome into `## Resolved Decisions`.

If an inconsistency turns out to hinge on a genuine business decision rather than a technical negotiation between the two sides, don't resolve it unilaterally here — take it back to `business-questions.md` (Phase 3) instead.

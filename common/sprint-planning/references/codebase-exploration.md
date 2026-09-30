# Phase 1 reference — Codebase exploration → `codebase.md`

## Purpose

`codebase.md` is the architecture reference every later phase leans on: scope judgments in Phase 3 cite it, the dev plan in Phase 4 references its file paths, and the task breakdown in Phase 6 points at the exact identifiers it names. Get it precise — file paths and identifier names matter more than prose explanation, since other phases quote it directly.

## Exploration scope is asymmetric — read this before deciding what to explore

This skill only ever produces a `tasks.md` for the repo it's running in — a frontend repo never gets backend tasks, and vice versa. The counterpart repo is treated very differently depending on which side you're on:

- **Running in a frontend repo**: explore this repo as the primary subject — that's where the plan and tasks live. Also explore the counterpart backend repo *if reachable on disk*, but **only** so that (a) you understand the business/domain well enough to judge scope and write a plan that makes sense, and (b) if the sprint needs an API contract proposal (Phase 5), that proposal is realistic against what the backend can actually support rather than invented in a vacuum. The backend exploration is context, not a parallel planning subject — never derive backend tasks from it, never write backend implementation detail into the dev plan beyond what the frontend needs to know about the contract.
- **Running in a backend repo**: explore only this repo. Do not explore a frontend counterpart even if one is reachable on disk. The frontend depends on the backend's contract; the backend does not depend on how any particular frontend consumes it, so frontend implementation details (component structure, form fields, UI state) have no bearing on backend planning and would only add noise.

## When to do a full sweep vs. an incremental update

- **No `codebase.md` exists yet anywhere under `docs/plans/sprint-*/` for this repo**: this is the first sprint planned with this skill here. Do a full sweep, even if some other loose architecture-description file happens to exist elsewhere in the repo (it wasn't produced by this process, don't assume it's still accurate or complete).
- **A `codebase.md` already exists from a prior sprint**: read it, plus that prior sprint's `stories-plan.md`/`<feature>-plan.md` and `tasks.md`. Those tell you what was actually planned and (assuming the tasks got checked off) built. Use them as a diff hint: only re-explore the specific areas the *new* sprint's stories touch, and update `codebase.md` in place rather than regenerating it from scratch. If the delta looks large (e.g. it's been many sprints, or the prior plan clearly diverged from what shipped), fall back to a fuller re-sweep of the affected areas.

## How to run the sweep

- **First, apply the asymmetry rule above to decide what's even in scope.** In a backend repo, stop here — there is no counterpart to detect or explore, skip straight to exploring this repo alone.
- **In a frontend repo**: detect whether the counterpart backend repo is reachable on disk. Check sibling directories at the same level as the current repo first; if not obviously present, ask the user for its path rather than assuming it doesn't exist.
- Use the `Agent` tool with `subagent_type: Explore`, launched in parallel (single message, multiple tool calls) — one agent for this repo, and (frontend repos only, when a backend counterpart is reachable) one more for the backend. Each agent needs a self-contained prompt: what the sprint's stories are about (so it knows what to look for), and the specific numbered areas to report on (see below). Run them in the background and continue other setup while waiting; don't poll.
  - **The backend agent's prompt (frontend repos only) should say explicitly that this is context-gathering, not backend task planning** — it exists so the plan judges scope correctly and any API proposal is realistic, not so backend implementation work gets defined. Brief it to prioritize the actual source code over any living/BRD-style docs in that repo (READMEs, contract docs, planning markdown) — those can go stale, and code is the source of truth for what currently exists.
- Cover, per repo, whatever of the following actually applies to the sprint's stories — skip areas with no bearing on this sprint rather than exhaustively documenting the entire codebase every time:
  - Overall structure and routing
  - State management / API layer (RTK Query slices, or backend controllers/services) — list actual endpoint names, request/response shapes, and where types live
  - Domain model and enums relevant to the stories (exact member names and values, not paraphrased)
  - Existing UI/API patterns closest to what the stories ask for (forms, modals, lookups, tables, integrations) — so later phases reuse rather than reinvent
  - Permissions/roles if the stories touch role-gated behavior
  - i18n conventions if the stories add user-facing text
- For anything a story describes that does **not** yet exist in the code, say so explicitly ("NOT FOUND") rather than guessing or inferring it might exist. This is what lets Phase 3 correctly judge scope instead of assuming everything described in a story is already half-built. In a frontend repo, gaps found on the backend side (missing endpoints, missing fields, missing integrations) are exactly this — "NOT FOUND" facts to plan an API proposal around, never implicitly treated as this sprint's work to do.

## Output structure

- **Frontend repo**: one `codebase.md`, organized by repo (e.g. `## 1. Frontend (repo-name)`, `## 2. Backend (repo-name) — context only`), each with numbered subsections matching the areas explored. Label the backend section clearly as context/reference so nobody later mistakes it for a second planning subject.
- **Backend repo**: one `codebase.md`, covering only that backend — no frontend section at all.
- Either way: precision over prose. Concrete file paths, exact identifier names, and endpoint routes, not general descriptions of what a layer "does."

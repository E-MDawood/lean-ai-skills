---
name: sprint-planning
description: >
  Use this skill to plan a sprint or a set of Jira user stories end to end, from
  raw story capture through implementation and code quality. Trigger on planning
  language: "plan this sprint", "plan these stories", "let's scope sprint N",
  "continue planning sprint N", or pasting Jira links specifically to plan/scope
  them (not to estimate their duration - that's the separate `estimation` skill).
  Also trigger when the user asks to pick back up on an in-progress sprint plan,
  or references docs/plans/sprint-<N>/ files.
---

# Sprint Planning Skill

Plans a sprint end to end across 8 phases, one durable markdown file per concern, living in `docs/plans/sprint-<N>/`. This skill is **phase-aware**: it does not run every phase every time it's invoked. It figures out where a sprint currently stands and continues from there, so the user never has to re-explain the current state.

Detailed rules for each phase live in `references/` — read the relevant reference file when you reach that phase, don't try to hold all of it in your head at once.

---

## Step 0 — Establish context and detect the current phase

1. **Detect project type.** Frontend: `package.json` with React/Vue/Angular/Vite/Next.js deps, or `vite.config.*`/`next.config.*`. Backend: `*.csproj`/`*.sln` (or equivalent backend project files). This affects two things later: Phase 1's exploration scope (see the asymmetry rule below — frontend repos also explore the backend counterpart for context, backend repos never explore a frontend counterpart), and Phase 4 includes a Frontend-only "Static Resources" section or a Backend-only "Architecture Diagrams" section as applicable.

   **Exploration scope is asymmetric, and this matters for every later phase, not just Phase 1.** The frontend depends on the backend's contract; the backend does not depend on how the frontend renders anything. So:
   - **Running in a frontend repo**: explore the frontend (primary — this is where the actual work and `tasks.md` live) *and* the backend counterpart, but the backend exploration exists **only** to understand the business/domain and to make sure any API contract proposal (Phase 5) is realistic against the backend's actual structure. It is never a source of backend tasks for this repo's `tasks.md`, and `codebase.md` should read as "here's what I need to know about the backend to plan the frontend well," not as a full backend architecture doc in its own right.
   - **Running in a backend repo**: explore only the backend. Do not explore a frontend counterpart, even if one is reachable on disk — how the UI is implemented is irrelevant to backend planning, since nothing on the backend side depends on it. `codebase.md` covers the backend only.

2. **Determine the sprint folder.** If a sprint number or `docs/plans/sprint-<N>/` path is already established in this conversation, reuse it — don't re-ask. Otherwise, ask the user for the sprint number and the Jira story links/keys for that sprint (ask both together in one message, not separately).

3. **Detect the current phase.**
   - **Same conversation, phase already tracked**: continue from conversation memory. Don't re-derive from files — you already know where things stand.
   - **New conversation, or asked to check**: inspect `docs/plans/sprint-<N>/` and infer the phase purely from which files exist and their content:
     | Signal | Phase to resume at |
     |---|---|
     | No `codebase.md` anywhere in `docs/plans/sprint-*/` for this repo yet | Phase 1 (first-ever run) |
     | `codebase.md` exists (this or a prior sprint), no `stories.md` for this sprint | Phase 1 (incremental update) → Phase 2 |
     | `stories.md` exists, `business-questions.md` missing or has unresolved items, no explicit override given | Phase 3 |
     | `business-questions.md` fully resolved (or user explicitly said proceed anyway), no `stories-plan.md`/`<feature>-plan.md` | Phase 4 |
     | Dev plan exists, sprint involves an API contract change, contract file missing or `api-changes-inconsistencies.md` has unresolved rows | Phase 5 |
     | Dev plan complete and self-contained, any contract inconsistencies resolved, no `tasks.md` | Phase 6 |
     | `tasks.md` exists with unchecked items | Phase 7 |
     | All tasks in `tasks.md` checked | Phase 8 |
   - **Always announce the inferred phase** and a one-line summary of what already exists (e.g. "Sprint 6 already has `codebase.md` and `stories.md`; `business-questions.md` has 4 open items across 2 stories — continuing the clarification round.") before proceeding, so the user can correct it if it's wrong.
   - **If `docs/plans/sprint-<N>/batches/` exists**, the sprint is batched — phase-detect per batch folder instead of against the sprint-root `stories-plan.md`/`tasks.md` (those are just the overview now, see `references/batching.md`), and report status per batch in the phase announcement (e.g. "batch-1 is at Phase 7, batch-2 is at Phase 4, batch-3 hasn't started").

4. Track phase progress for the session with `TodoWrite`, one item per phase, so progress is visible as you move through them.

5. **Reopening is normal, not an error.** If at any later phase (4 through 7) a genuinely new ambiguity surfaces, drop back into Phase 3 for that item: add it to `business-questions.md`, resolve what can be resolved, and explicitly flag to the user whether it affects plan content already written. Don't treat Phase 3 as "done forever" once you've moved past it.

6. **Once `business-questions.md` is clear enough to move into Phase 4, always ask the user whether delivery should be batched or all together** — never assume either way, even if the sprint looks small or the stories look tightly coupled. See `references/batching.md` for what batching changes about file layout and how to phase-detect against it.

---

## Phase 1 — Codebase exploration → `codebase.md`

- **First time this skill is used in this repo** (no `codebase.md` exists yet anywhere under `docs/plans/sprint-*/`): run a full exploration of this repo. **In a frontend repo only**, also explore the counterpart backend repo if it's reachable on disk (check sibling directories, ask the user for the path if it's not obvious) — for business/domain context and to ground any later API proposal in the backend's real structure, not to plan backend work. **In a backend repo, skip exploring any frontend counterpart entirely** — it has no bearing on backend planning. Write a fresh `codebase.md`: two sections (frontend + backend context) when in a frontend repo, backend-only when in a backend repo.
- **A `codebase.md` already exists from a prior sprint**: don't blindly re-explore everything. Read the old `codebase.md` plus the prior sprint's `stories-plan.md`/`tasks.md` (what was actually planned and presumably built), use them as a map of what's likely changed, and re-explore only the areas implicated by the new sprint's stories. Update `codebase.md` in place rather than rewriting it from scratch, unless the delta turns out to be large. The same asymmetry applies to incremental updates too — a backend repo's `codebase.md` should never grow a frontend section.
- See `references/codebase-exploration.md` for what to cover and how to structure the file.

## Phase 2 — Story capture → `stories.md`

- Fetch every linked story in full via `mcp__atlassian__getJiraIssue` (or ask the user to paste it if MCP isn't available/fails — don't skip a story silently).
- Write it verbatim. No scope notes, no judgment, no added commentary of any kind — this file is the raw source of truth, nothing else.
- See `references/story-capture.md` for the exact section structure.

## Phase 3 — Scope judgment and clarification → `analysis-notes.md` + `business-questions.md`

- Judge each story's frontend/backend impact from `codebase.md` plus business logic. **Never use a story's Jira labels to decide scope** — they're unreliable; judge from what the code and the story's actual content say.
- If `docs/plans/<sprint-folder>/brd.pdf` exists, read it before raising a question — it's the sprint's Business Requirements Document, and Jira story text is often a compressed summary of what it actually specifies, including figures and attachments the story text leaves out entirely.
- Run an iterative clarification round via `AskUserQuestion` (batches of up to 4 questions) surfacing genuine contradictions, undefined terms, and fields that don't map to anything in the current code. This is not one-shot — see Step 0.5 above.
- Full rules, including the exact writing style required for `business-questions.md` (it gets shared outside the engineering team), live in `references/clarification-round.md`. Read it before writing either file.
- **Gate**: don't start Phase 4 for a story while it still has unresolved items in `business-questions.md`, unless the user explicitly says to proceed anyway.

## Phase 4 — Detailed development plan → `stories-plan.md` or `<feature>-plan.md`

- Use `stories-plan.md` when planning all of a sprint's stories together; use a descriptive `<feature-or-domain>-plan.md` when grouping by feature/domain/dependency instead. **If the sprint is batched (see item 6 above and `references/batching.md`), each batch gets its own `stories-plan.md` under `docs/plans/sprint-<N>/batches/batch-<M>/`, and the sprint-root `stories-plan.md` becomes a cross-batch status/overview file instead.**
- Pulls from `analysis-notes.md`'s resolved decisions — never re-derives them, never duplicates raw story text from `stories.md` or open items from `business-questions.md`.
- See `references/dev-plan-format.md` for section structure and the self-containment rules (exact enum values, field names, endpoint paths — no vague verbs like "update"/"support" without specifics).
- **Gate**: once written, this plan gets reviewed by a fresh subagent before moving on — this is the file that turns directly into code, so it's the highest-leverage place in the whole skill for a review pass. See "Plan review before moving on" in `references/dev-plan-format.md`.

## Phase 5 — API contract files (only when the sprint changes a contract)

- First determine whether backend has already built/specified the relevant endpoints (Swagger is the source of truth, propose only for genuine gaps) or hasn't yet (write a full proposal). Ask if the user's prompt doesn't already make this clear — don't assume.
- `frontend-to-backend-api-changes.md` (frontend-owned proposal) or `backend-to-frontend-api-changes.md` (backend-owned proposal), plus `api-changes-inconsistencies.md` once both sides' proposals are compared. **If batched, these live inside the batch folder that actually needs them (`docs/plans/sprint-<N>/batches/batch-<M>/`) — not every batch needs one.**
- See `references/api-contract-format.md`.

## Phase 6 — Task breakdown → `tasks.md`

- Only after Phase 4's plan is complete and self-contained, and Phase 5's inconsistencies (if the sprint had any) are resolved.
- Dependency-ordered, one task per concrete unit of work, plain markdown checklist — this repo doesn't use Task Master AI (referenced in root `CLAUDE.md` but never actually set up; revisit only if that changes separately from this skill).
- **If batched, each batch gets its own `tasks.md` under its `batches/batch-<M>/` folder, in the same format as the non-batched case; the sprint-root `tasks.md` becomes a cross-batch status/overview file instead.**
- See `references/task-breakdown-format.md`.

## Phase 7 — Implementation

- Execute `tasks.md` in dependency order, checking items off as they're completed.
- Follow this repo's existing conventions and skills for the kind of work each task is (forms, vitest, mock-server, etc. — whichever apply).

## Phase 8 — Quality gate

- Before calling a story or the sprint done: focused tests, lint, a `fallow` self-review pass on changed files, `review`/`security-review` where warranted, i18n check (both languages), and verification of required/read-only/loading/error states.
- Also run a **plan-fidelity check**: a fresh subagent comparing the actual implementation against the plan (not just against quality standards) — catches drift from intent that tests/lint/review wouldn't. See "Plan-fidelity check" in `references/quality-gate.md`.
- **Frontend only**: also run the **UI validation** check — launch the app headless (`run` skill first, `browser-check` as the fallback if `run`'s preferred tool isn't available), screenshot the surface, compare against the design (or the intended look if there wasn't one), same context as the implementation (not a fresh subagent, unlike the plan-fidelity check). If the app needs SEHA auth specifically, use the `seha-auth` skill rather than improvising a login workaround. See "UI validation (frontend only)" in `references/quality-gate.md`.
- See `references/quality-gate.md`.

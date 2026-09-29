---
name: bug-fixer
description: Use this skill when fixing a bug reported in QA, Staging, or Production. Accepts a Jira ticket link or a plain description of the issue. Fetches ticket context, searches for any associated planning files across all sprints, then diagnoses and fixes the issue. Asks clarifying questions whenever context is ambiguous.
---

# Bug Fixer

Fix a reported bug using whatever context is available: Jira ticket details, planning docs, story attachments, and reference material. All docs are optional — load what exists and proceed regardless. Ask questions freely — a wrong diagnosis is worse than a slow one.

---

## Step 0 — Detect which side this repo is

Before diagnosing anything, determine whether the current repo is frontend or backend, so a bug that actually belongs to the other side can be identified as such rather than forced into a fix here:
- **Frontend**: `package.json` with a React/Vue/Angular/Vite/Next.js dependency, or a `vite.config.*`/`next.config.*` file.
- **Backend**: `*.csproj`/`*.sln` (or the equivalent backend project files for the stack in use).

Keep this in mind through Step 3 — it's what makes the "wrong side" check there possible.

## Step 1 — Gather the issue context

### If a Jira link is provided:
Fetch the ticket using the Atlassian MCP. Extract:
- Title and full description
- Steps to reproduce
- Environment label (QA / Staging / Production)
- Sprint or fix version if present
- Any attachments or linked resources
- Comments that clarify the issue

### If only a description is provided:
Use what the user has given. Ask for the Jira link or for reproduction steps if they are missing and the issue cannot be clearly located in the codebase without them.

### Ask upfront if unclear:
Before proceeding, ask the user any of the following if the answer is not available from the ticket or description:
- Which environment was the bug found in? (QA / Staging / Production)
- **What is the current sprint number?** — always ask this if the sprint cannot be determined from the ticket. The sprint number is needed to locate the right planning docs (see Step 2 for where these live).
- Is this related to a specific sprint, feature, or recent change?
- Are there attachments, screenshots, or logs that help reproduce it?

---

## Step 2 — Load available context

All files below are optional. Load what is present and skip what is not — their absence never blocks the next step.

**Planning docs** — if a `docs/plans/` directory exists, locate the sprint folder for the sprint number from Step 1. The standard layout is `docs/plans/sprint-<number>/`, but some repos group sprints under a domain or project subfolder instead, e.g. `docs/plans/<domain>/sprint-<number>/` — don't assume either layout, search for a `sprint-<number>` folder anywhere one level or two levels under `docs/plans/`. If the sprint number is unknown, or several `sprint-<number>` folders match across different domain subfolders, use the Jira key, story title, project/component, or affected feature to pick the most relevant one, and prefer the most recently modified if still ambiguous.

Whichever folder it turns out to be, look for these files inside it:

```
codebase.md                          ← map of the relevant code, endpoints, and patterns at planning time
stories.md                           ← the story captured exactly as written, verbatim
analysis-notes.md                    ← resolved scope decisions and the internal reasoning behind them
business-questions.md                ← open questions raised during planning and how they were resolved
stories-plan.md                      ← intended behavior per story
<feature>-plan.md                    ← feature/domain-scoped plan, used instead of stories-plan.md when the sprint was grouped that way
frontend-to-backend-api-changes.md   ← API contract changes proposed by the frontend
backend-to-frontend-api-changes.md   ← API contract changes proposed by the backend
api-changes-inconsistencies.md       ← mismatches found between the two proposals, and how they were resolved
tasks.md                             ← the dependency-ordered checklist actually followed during implementation
```

`codebase.md`, `stories.md`, `analysis-notes.md`, and `business-questions.md` give the scope and intent behind a story; `stories-plan.md`/`<feature>-plan.md` and `tasks.md` give the concrete implementation that was supposed to happen. Read both groups when available — a bug is often a gap between the two. In a backend repo, only backend-relevant files will exist (there's no frontend counterpart to look for); in a frontend repo, the reverse — treat any of these as optional, not a fixed checklist every project must have.

**Story attachments** — if present, check for the relevant story key or range:
```
docs/stories/<story-key>/
docs/stories/<story-key-range>/
```

**Reference material** — load if present:
- `docs/designs/` — UI designs *(frontend)*
- `docs/diagrams/` — architecture diagrams *(backend)*
- `docs/api/swagger.json` — API contract reference

When planning docs are found, read them before touching any code — the bug may be a deviation from the plan, a contract mismatch, or a regression from an adjacent change, and understanding the intent first prevents fixing in the wrong direction.

---

## Step 3 — Diagnose the issue

With full context loaded:

1. Locate the code path related to the bug using the reproduction steps and any available planning docs.
2. **Check whether this is actually a bug.** Compare the reported behavior against the code and, where available, `business-questions.md`, `analysis-notes.md`, and `stories-plan.md`/`<feature>-plan.md`. A report is sometimes a misunderstanding by the reporter rather than a real defect, a condition that's intentionally there, a documented limitation, or behavior that matches what was actually planned. Reason from concrete evidence, not by default suspicion of every ticket.
   - If the code or planning docs show the reported behavior is intentional, or the evidence is genuinely ambiguous, or fixing it could affect other intended behavior: stop here and tell the user plainly, citing the specific evidence, e.g. *"This might not be a valid issue, the code has this condition in place intentionally because \<reason\>. Do you still want it changed? It could break \<specific behavior\>."* Wait for their answer before continuing.
   - Only move on once the bug is confirmed real, either because the evidence is clear or because the user has explicitly confirmed they want the change made anyway.
3. Identify the root cause — do not fix symptoms.
4. Classify the bug:
   - **Plan deviation** — implementation did not follow what was planned
   - **Contract mismatch** — API shape, field name, or enum value differs between frontend and backend
   - **Regression** — a change in a later sprint broke previously working behavior
   - **Logic error** — a genuine code bug not tied to a planning gap
   - **Environment-specific** — only fails in QA / Staging / Production due to config, data, or infra differences
5. If the root cause is a contract mismatch, flag it clearly before fixing — the fix may need coordination with the other side.
6. **Check whether the root cause actually lives in this repo.** Using the side detected in Step 0:
   - **Running in a frontend repo, but the root cause is on the backend** (wrong data returned, a missing/broken endpoint, server-side validation, etc.): stop, do not attempt a backend fix from here. Tell the user this is most likely a backend issue, with the specific reason why, and offer to confirm it by exploring the backend repo, read-only, if they provide its path — that pass is only to confirm or refute the root cause, never to fix it there; any actual fix in that repo is a separate action the user takes themselves.
   - **Running in a backend repo, but the root cause is on the frontend** (a client-side rendering, state, or validation bug the backend can't fix): stop, do not attempt a frontend fix from here. Tell the user this is most likely a frontend issue, with the specific reason why, and offer the same read-only confirmation pass against the frontend repo if given its path.
   - Only continue to Step 4 once the root cause is confirmed to belong to the side this repo actually is.

**Ask before proceeding if:**
- The correct intended behavior is ambiguous in both the code and the planning docs, with no clear evidence either way
- It's unclear which side (frontend or backend) actually owns the root cause

---

## Step 4 — Fix the issue

Apply the fix:

- Follow the existing patterns, conventions, and style in the codebase.
- Do not refactor or clean up code outside the direct scope of the bug.
- Do not add new features or extend behavior beyond what restores the intended functionality.
- If the planning doc is ambiguous about the correct behavior, state the assumption explicitly before applying the fix.

Update tests:
- Fix any existing tests broken by the change.
- Add a focused test that would have caught this bug.
- Run affected tests: `pnpm test <affected-files>` *(frontend)* or the equivalent test command for the project.

---

## Step 5 — Summarize the fix

```
Bug: <one-line description>
Environment: QA | Staging | Production
Root cause: <what was wrong and why>
Fix: <what was changed and where>
Planning reference: <path to the planning file that informed the fix>  ← omit if no relevant docs found
Tests: <what was added or updated>
Follow-up needed: <note if a contract fix or cross-team coordination is required>
```

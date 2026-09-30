# Phase 4 reference — Detailed development plan → `stories-plan.md` / `<feature>-plan.md`

## Choosing the file

- Default to `stories-plan.md` when planning all of a sprint's stories together.
- Use a descriptive `<feature-or-domain>-plan.md` (e.g. `report-categorization-plan.md`, `permissions-plan.md`) when stories are better grouped by feature, domain, or dependency instead — a sprint can have several of these side by side.
- Plan story-by-story (one section at a time, checking in with the user) when a story needs heavy clarification or has many dependencies; plan multiple stories together in one pass when they're simple, already clear, or tightly coupled.

## Section structure

```
# Sprint <number> Development Plan        (or # <Feature/Domain> Development Plan)

## Summary

## <Jira key>: <Story title>
### Implementation Changes                (### Frontend Changes / ### Backend Changes when the project type adds clarity)
### Data / Metadata / Contract Details     (when needed)

## <next story>
...

## Test Plan
## Confirmed Decisions
```

For a shared multi-story file:
- All story sections come before the closing cumulative sections.
- `## Test Plan` comes before `## Confirmed Decisions`.
- When appending a new story later, insert it before the closing sections, then update `## Test Plan` and `## Confirmed Decisions` to reflect it (don't skip this just because the new story seems simple — check deliberately).

## No separate "Business Requirements Questions" section here

Earlier versions of this planning guide had a `## Business Requirements Questions` section inside the dev plan itself. This skill handles that differently: `business-questions.md` (Phase 3) is the single, sprint-level home for open business questions, not per-plan-file. By the time a story's section gets written here, its items in `business-questions.md` should already be resolved (that's the Phase 3 → Phase 4 gate). If something new comes up *while* writing this plan, don't note it inline here — go back to `business-questions.md` and add it there (see "Reopening is normal" in `SKILL.md`), then come back and finish this section once it's resolved.

`## Confirmed Decisions` in this file is a different kind of decision than what lives in `analysis-notes.md`: `analysis-notes.md` records *requirements-scope* decisions (what a story actually means, which field maps to what). `## Confirmed Decisions` here records *implementation-approach* decisions made while writing the plan itself (e.g. "extracted a shared hook for X rather than duplicating the popup logic," "chose approach A over B for the admission-details form"). Keep them separate — don't let one drift into duplicating the other.

## Self-containment rules

Every story section must let an implementer work from it without needing the chat history or re-reading the original Jira ticket:

- Exact enum values, type names, field names, endpoint paths, labels, file paths, and fallback behavior, whenever they're relevant.
- Known out-of-scope items, stated explicitly.
- Confirmed zero-state/empty-state behavior.
- **No vague planning verbs alone** — "update," "adjust," "support," "handle" must always come with the specifics of *what* changes and *how* it should behave. "Update the close-reason field" is not a spec; "replace the free-text close-reason input with a dropdown bound to the new Close Reason lookup, submitting the reason's numeric id" is.
- When a story affects existing logic, describe the concrete implementation direction: exact requiredness rules, field names, enum values, helper behavior, routing behavior, render conditions, endpoint usage — not just the intent.
- For workflow-heavy stories, write the workflow path out as text in the plan when implementation depends on flow diagrams, screenshots, or attachments, so the plan stays implementation-ready even if the implementer never reopens the original images.
- When a plan changes a filter, size limit, naming format, or validation rule, state the exact values and exact touchpoints, not just "update" or "support."

## Plan review before moving on (gate)

This is the highest-leverage review point in the whole skill — this file is what gets translated directly into code, so it needs to be as flawless as possible before that happens.

Once the plan is fully written (for a story, or the whole file), review it before moving into Phase 5/6. Use the `Agent` tool to run this in a **fresh context** — a subagent with no memory of having written the plan, given the plan itself plus `analysis-notes.md`, `business-questions.md`, and `codebase.md`. Frame the prompt adversarially: assume something in this plan is wrong or incomplete and find it, not "does this look right." A same-context re-read tends to just confirm its own work; a fresh reviewer with no attachment to it catches more.

Checklist for the reviewer:

- Any vague verb ("update," "support," "handle," "adjust") without the concrete specifics stated right next to it.
- Any field, enum, endpoint, or component name that doesn't actually exist in `codebase.md` and isn't explicitly marked as new.
- **Any section proposing a new component, hook, or pattern when `codebase.md` already documents an existing one that covers the same need** — the plan should say reuse/extend, not reinvent.
- Any plan section that leans on "as discussed" instead of restating the actual decision inline — would an implementer with zero chat history be stuck here?
- Any place the plan's wording drifts from what `analysis-notes.md` actually resolved — restated slightly wrong from memory instead of matching the source.
- Any place the plan silently assumes an answer to something still open in `business-questions.md`.
- Internal contradictions between two sections of the plan itself (the same field given two different rules in two places).
- Missing zero-state/empty-state/out-of-scope statements where the format above calls for them.

**Gate**: don't move into Phase 5/6 while the reviewer's findings are unresolved. Fix what's found, and re-run the check on anything substantially rewritten as a result. Re-run this same review any time the plan is amended later (e.g. a reopened Phase 3 question changes something already written).

## API contract awareness (Frontend only)

When a story requires static client-side resources (e.g. report templates), treat the confirmed folder/resource structure as the frontend source of truth. Include exact metadata needed for implementation (labels, paths, enum values, fallback behavior). If a referenced folder is missing and the user confirms that means zero items, document the zero-item case explicitly rather than leaving it implicit.

## Architecture diagrams (Backend only)

When a story involves system or service design, store diagrams in `docs/diagrams/` and reference them from the relevant story section, but include enough textual description in the plan itself that an implementer doesn't need to open the diagram to understand the approach.

# Batching reference — splitting a sprint's delivery into batches

## When to ask

Once `business-questions.md` is clear enough to move into Phase 4 (the normal Phase 3 → Phase 4 gate), **always ask the user whether they want delivery batched or all together**, before writing any Phase 4 file. Never assume either way — not even when the sprint is small, the stories look tightly coupled, or a batching scheme was discussed earlier in the same conversation for a different sprint. Ask again per sprint.

A sprint moving into Phase 4 for the first time and a sprint that later needs its batching scheme changed both go through this same question — batching is a delivery-organization decision, not a one-time setup step, so revisit it if the user brings up different batches or deadlines later.

If the user says no batching, proceed exactly as documented elsewhere in this skill (a single `stories-plan.md`/`tasks.md`, or `<feature>-plan.md` files, directly under `docs/plans/sprint-<N>/`) — everything below only applies once they say yes.

## What batching changes

Batching doesn't change *what* gets planned, only *how the output files are organized* — each batch is a self-contained slice of the sprint, plannable and deliverable independently of the others, with its own timeline.

Ask the user how they want stories grouped into batches (a batch can hold one story or several — group by shared implementation, dependency order, or whatever delivery grouping they name) and what order/timing applies to each, then confirm it back before creating files.

## File layout

```
docs/plans/sprint-<N>/
  stories.md                     (unchanged — still sprint-wide, not per batch)
  codebase.md                     (unchanged — still sprint-wide, not per batch)
  analysis-notes.md               (unchanged — still sprint-wide, not per batch)
  business-questions.md           (unchanged — still sprint-wide, not per batch)
  stories-plan.md                ← now an OVERVIEW file, not the dev plan itself
  tasks.md                        ← now an OVERVIEW file, not the task list itself
  batches/
    batch-1/
      stories-plan.md            (this batch's Phase 4 dev plan, same format as the non-batched case)
      tasks.md                    (this batch's Phase 6 task list, same format as the non-batched case)
      frontend-to-backend-api-changes.md   (only if this batch needs a Phase 5 contract file)
    batch-2/
      stories-plan.md
      tasks.md
    ...
```

- Phases 1–3 (`codebase.md`, `stories.md`, `analysis-notes.md`, `business-questions.md`) **stay sprint-wide** — they're not duplicated or split per batch, since they cover shared understanding the whole sprint draws on.
- Phases 4–6 outputs move into `batches/batch-<M>/`, one subfolder per batch, using the **exact same file names and formats** documented in `references/dev-plan-format.md`, `references/api-contract-format.md`, and `references/task-breakdown-format.md` — nothing about those formats changes, only where the files live.
- Only create the Phase 5 contract files inside a batch folder if that specific batch actually changes a contract — not every batch needs one.
- Number batches in delivery order as the user defines it (`batch-1`, `batch-2`, ...), not necessarily in Jira key order.

## The sprint-root overview files

With batching, `docs/plans/sprint-<N>/stories-plan.md` and `docs/plans/sprint-<N>/tasks.md` stop holding the actual plan/task content — that content lives per batch instead. Instead, these two files track cross-batch status:

- Which stories are in which batch.
- Each batch's current phase (planning / contract / tasks / implementing / done) and expected delivery timing, as the user defined it.
- A link to each batch's `stories-plan.md` and `tasks.md` (and contract files, if any).
- What's implemented so far and what isn't, kept current as batches progress through Phase 7/8 — this is what makes these two files useful as a standalone "where does the sprint stand" reference without having to open every batch folder.

Update these overview files whenever a batch's phase or status changes — don't let them go stale while the per-batch files keep moving.

## Phase detection with batching

Once `docs/plans/sprint-<N>/batches/` exists, phase-detect **per batch folder**, not against the sprint-root `stories-plan.md`/`tasks.md` (Step 0's phase table in `SKILL.md` still applies, just run it once per batch folder). Report status per batch when announcing the inferred phase, and let the user resume a specific batch by name.

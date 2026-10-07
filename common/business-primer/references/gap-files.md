# Gap files (Phase 3)

Three files, different audiences. If the repo has a `sprint-planning` skill, follow its file names and folder; otherwise use `docs/business/`.

## `analysis-notes.md` (internal)

- How the scope is shaped (architecture-level facts that change how stories should be read).
- Impact per story.
- **Decisions** D1, D2… with the reason, so nobody re-derives them.
- **Working assumptions** table: topic, the assumption used for planning, the question ID it depends on.
- Cross-story observations (shared validators, shared clients, real overlaps only).

## `business-questions.md` (shareable with the business)

Style rules, because people outside engineering read it:
- One `##` section per story: `## KEY - Title`.
- Numbered questions, each stating the evidence briefly and the working assumption in hedged words ("We are assuming… Is that correct?").
- No file names or paths, no checkboxes, no em dashes, no "confirmed" language for things that are assumptions.
- Only genuine business questions. Technical choices (retry counts, rate limits, storage, algorithms) go to `analysis-notes.md` as decisions. Planning concerns (missing sprint rows, estimates) go to the team lead, not the BA.
- When a question is answered: move it to a decision in `analysis-notes.md`, remove it here, renumber, and update every reference to the old numbers.

## `brd-context-and-business-gaps.md` (team reference)

- Sources and their precedence.
- Business context summary (actors, integrations, core rules, statuses, code lists).
- Gap table per plan item: status (closed / open / new), detail with source IDs, what earlier feedback said.
- Open items list, parked items per later sprint, change log with dates.

## Rules for every gap entry

- Cite the source ID; quote the exact text when wording matters.
- Label written vs implied vs assumed.
- Re-check the source before logging; don't log a simplified diagram as a contradiction.
- Every inconsistency found while answering a user's question gets logged too, and you tell the user where.

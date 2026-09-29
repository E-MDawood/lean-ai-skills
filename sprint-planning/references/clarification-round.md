# Phase 3 reference — Scope judgment and clarification → `analysis-notes.md` + `business-questions.md`

This is usually the longest, most iterative phase. Jira stories are frequently contradictory, use undefined terms, or describe fields that don't map to anything in the actual code. Don't try to resolve everything yourself, and don't dump everything on the user either — triage.

## Judging scope

- Judge each story's frontend/backend impact from `codebase.md` plus what the story's own content actually says. **Never use a story's Jira labels (e.g. `FrontEnd`, `backend`) to decide scope** — they're frequently wrong. A story labeled `backend`-only can turn out to be almost entirely frontend work (a mandatory UI popup, say), and a story labeled `FrontEnd` can turn out to need no frontend changes at all (e.g. it's the display-side companion to an inbound API another story defines). Judge from evidence, not the label. This "judge impact on both sides" framing is for when the skill is running **in a frontend repo** (per Phase 1's asymmetry rule, `codebase.md` there includes backend context precisely so this judgment call can be made correctly). When running **in a backend repo**, there is no frontend counterpart to weigh — judge backend scope only, and don't speculate about what a frontend would or wouldn't need to build around it.
- When several stories in the same sprint describe integration APIs (one system calling another), don't assume the frontend needs to call any of them directly — check whether the frontend already has its own separate endpoints for the equivalent internal action first. It's common for a sprint to build endpoints that an *external* system calls, while the frontend keeps using its own existing (or lightly modified) endpoints and only needs to reflect whatever data ends up in the database. Confirm this split explicitly with the user rather than assuming either way.
- Not every field that appears in an API contract needs a UI counterpart. Some fields exist purely for backend/database reference or cross-system compatibility and are never entered or displayed anywhere. When judging whether a story needs new form fields or new display fields, ask "does this need a UI counterpart" as a distinct question from "does this field exist" — don't conflate the two into "the API story implies a form field" (the wrong assumption to make) or "the API story implies zero frontend work" (the other wrong assumption). Distinguish, if relevant, between what belongs on a **creation form** versus what belongs on a **view/detail page** — a view page can need more fields than the form (e.g. externally-sourced-only fields, or read-only computed data), but should never need fewer than whatever the form captures.
- Don't flag two stories as "overlapping" or "needing joint planning" just because they happen to name similar-sounding fields. Check first whether the two stories actually live in the same implementation lane (same file, same API, same UI flow) — if one is a backend-only integration contract and the other is a frontend feature with its own independent implementation, matching field *names* doesn't mean they're coupled. Only call out a real overlap when the same underlying field/lookup/model genuinely needs to be shared or kept consistent across both.

## Check for existing answers before asking

Before raising a question, check whether it's already answered locally: `docs/designs/` (screenshots and visual notes, frontend), `docs/stories/<story-key-or-range>/` (story-specific attachments of any kind), and `docs/plans/<sprint-folder>/brd.pdf` (the sprint's Business Requirements Document, when one exists) may already contain the answer — a screenshot of the actual UI, a diagram, a spec document, a field or flow the BRD spells out that the Jira story text left vague. Read the BRD directly (PDF reading is a native capability, no extra setup needed) rather than skipping it because it's a PDF — it often carries detail, and sometimes figures/attachments, that the story text alone doesn't, and story text is frequently a compressed summary of what the BRD actually specifies. Inspecting these costs nothing and regularly resolves what would otherwise be a business question (this happened repeatedly in practice: a UI screenshot settled several "what does the existing behavior actually do" questions outright). Only ask the user or file something in `business-questions.md` once you've checked all of these and the code itself has nothing to say on the matter either.

## Actively cross-check designs against the story (frontend only, optional)

This is a step within this phase, not a separate one — it uses the same two output files and the same triage table below, just with a design file as the thing being compared against the story instead of another story or a code check. The section above is about consulting a design *passively* when a question already exists; this is the *active* counterpart: when a frontend story has an associated design in `docs/designs/` or `docs/stories/<key>/`, deliberately compare it against that story's text and acceptance criteria looking for contradictions, even when nothing has prompted a question yet. A field the design shows that the story text never mentions, a flow the design implies that the AC doesn't describe, a label or behavior that conflicts with what's written. Skip this entirely for stories with no associated design — don't force it.

Whatever it turns up goes through the same triage as everything else: the design clearly settles something and matches expectations → resolved decision in `analysis-notes.md`. The design conflicts with the story text in a way that needs a business/product call → `business-questions.md`, tagged `[Design]` (see the style rules below).

## Running the clarification round

- Batch questions via `AskUserQuestion`, **up to 4 per call**. Prioritize genuine ambiguities: internally contradictory acceptance criteria, undefined terms, fields with no home in the current model, and stories that reference a concept (a lookup list, a status, a field) another story also touches — check whether they mean the same thing or something different.
- Give every question 2-4 concrete options plus an explicit "not sure / need to check with product" (or equivalent) option — this makes it trivial for the user to signal "I don't know" without typing it out, and gives you a clean trigger for how to file the answer (see Triage below).
- **This is not a one-shot pass.** Expect the round to reopen after it feels "done" — a user reviewing your first pass will often surface entirely new angles (a missing distinction you hadn't drawn, a contradiction between two answers you gave earlier, a UI screenshot that resolves one question but reframes another). Treat every later message that raises a new angle as a legitimate continuation of this phase, not noise to route elsewhere. This can happen even after Phase 4-7 have started — see Step 0.5 in `SKILL.md`.
- If the user provides direct evidence (a screenshot of the actual UI, a code reference, an explicit business decision) that resolves a question with certainty, verify it against the actual code where possible (grep/read the relevant file) before treating it as settled — don't take a claim about "existing behavior" on faith when it's cheap to check.
- If the user already has their own pre-existing question list (from their own review, or their team/backend's review of the same tickets), merge it into `business-questions.md` rather than keeping two separate lists. Dedupe by topic, not by exact wording — the same underlying ambiguity phrased two different ways is one item, not two.

## Triage: where does each answer go?

| Answer | Goes to |
|---|---|
| Definitive answer, or resolved via evidence (screenshot, code check, explicit business decision) | `analysis-notes.md`, as a resolved decision with the reasoning. **Never** leave a resolved item sitting in `business-questions.md`. |
| "I don't know" / "not sure" / "need to check with product" / no answer given | `business-questions.md`. |
| User corrects, narrows, or expands a question you already asked | Edit that question in place in whichever file it currently lives in — don't leave the stale version alongside the new one, and don't just append the correction as a separate bullet. |
| A question turns out to be moot once a *different* question resolves (e.g. two questions both depended on the same unresolved field, and one of them got answered directly) | Remove it from `business-questions.md` and note the resolution (and why the other question is now moot) in `analysis-notes.md`. |
| User points out a question was based on a wrong premise or misunderstanding | Remove or rewrite it — don't leave a wrong question in the shared file just because it was asked once. Acknowledge the correction and re-derive the real question if one still exists. |

## Writing `analysis-notes.md`

Internal file — this is our own synthesis, not shared outside the team, so it can be as detailed and cross-referential as useful. Structure:

1. Short intro: what this file is, what it isn't (no business-owner input needed for anything in here), pointer to the sibling files.
2. **How this sprint is scoped** — the architecture-level facts that reshape how multiple stories should be read (e.g. "these 6 stories are endpoints we expose, not ones we call," "labels are unreliable for this sprint specifically because..."). These are usually the first things resolved and the most load-bearing for everything after.
3. **Frontend-impact judgment per story** — a table: story, impact (yes/no + rough size), one-line basis citing `codebase.md` or a resolved decision.
4. **Other decisions resolved this round** — a running list, one bullet per resolved item, each with enough reasoning that revisiting it later doesn't require reconstructing the "why" from scratch.
5. **Cross-story observations** — genuine overlaps, shared lookups/fields, inconsistencies between stories (e.g. mismatched file size limits between two stories describing similar upload behavior). Apply the "don't over-claim overlap" rule from above here specifically — this section is the one most prone to false-positive connections.

## Writing `business-questions.md`

**This file gets shared outside the engineering team**, with business/product. Its style constraints exist for that reason and are non-negotiable unless the user says otherwise:

- **No checkboxes.** Plain bullet points (`- `), not `- [ ]`. This isn't a task tracker, it's a document being read by people outside the process.
- **No em dashes anywhere**, including inside quoted story text — rephrase instead. Use commas, periods, colons, or "and"/"or" to join clauses.
- **No references to other internal files** — never mention `stories.md`, `analysis-notes.md`, `codebase.md`, or any file path. The business reader shouldn't need to know these exist. If a question needs context from `codebase.md`, restate that context in plain language inline instead of pointing at the file.
- **No assertive "confirmed" language.** Don't tell the business reader something "is confirmed" or "is certain" when what you mean is "this is what we're currently assuming." Use "assuming," "based on," or similarly hedged phrasing so it's clear these are working assumptions the business can correct, not settled facts being reported back to them.
- **One `##` section per story** (`## REDJ-XXX - Story Title`), each with its open items as plain bullets. A story with nothing open gets a single line: `Clear.`
- **Tag design-sourced questions.** Any item that came specifically from cross-checking a design/mockup against the story text (not from the written requirements alone) starts with `[Design]`, e.g. `[Design] The mockup shows a "Priority" field on this form that isn't mentioned in the story text. Should it be included?` This keeps them easy to tell apart from questions that come from the story text alone.
- No intro paragraph explaining the file's provenance ("surfaced during an AI-assisted review," dates, process notes) — the business reader doesn't need the backstory, just the questions.
- Every question should be genuinely open, i.e. something a business/product person, not an engineer, needs to answer. If a question is really "which existing lookup table should this reuse," that's an engineering decision for `analysis-notes.md`, not a business question.

## Gate before Phase 4

Don't start writing the detailed dev plan (Phase 4) for a story while it still has unresolved items under it in `business-questions.md`, unless the user explicitly says to proceed anyway. This mirrors the original planning guide's rule and exists to stop a plan from quietly building on top of an assumption that later turns out wrong.

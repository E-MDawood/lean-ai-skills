---
name: business-primer
description: Turn a project's raw business material (Jira user stories, use-case documents, a BRD, attachments, mockups, diagrams) into a complete, honest understanding of the business - extracted BRD notes, a gap analysis with business questions, and an interactive onboarding artifact whose tabs are chosen to fit the business (always overview, users, lifecycle and every value list, key rules, glossary, open points, extra clarifications; plus integrations, screens, calculations, workflow or other tabs when the business depends on them). Use this skill whenever someone wants to understand a new project's business, onboard to a project, "make sense of these stories / this BRD", map integrations or users from requirements, find gaps in requirements, or produce a primer, guide or explainer of a business domain - even if they only paste a few Jira links or say "I'm new to this project and understand nothing". Starts by collecting inputs; it does not jump straight to building the artifact.
---

# Business Primer

Takes the business of any project and turns it into something a newcomer can understand in an hour, and that the team can trust because every claim traces back to a source. The work happens in phases. **Do not build the artifact first.** A primer built on half the inputs looks authoritative and is wrong, which is worse than no primer.

## Phase 0: Intake (always first)

Goal: collect *everything* before analysing anything. Read `references/intake-checklist.md` and run it.

In short:
1. **Stories.** If the user gave none, ask for them (Jira links or keys, or exported files). Nothing else can start without them.
2. **For every Jira story, read the whole record**, not just the description: sub-tasks, comments (especially unanswered questions), linked issues, labels, status, the attachment list. Use the Atlassian connector if available (`getJiraIssue` with `fields: ["*all"]`, plus a JQL `parent = KEY` for sub-tasks, plus `getJiraIssueRemoteIssueLinks`). If the connector fails (for example 403 "app not installed"), say so plainly and ask the user to export or paste the stories, sub-tasks and comments.
3. **Attachments.** You cannot download Jira attachments. List the attachment names you saw and ask the user to place each in `docs/stories/<STORY-KEY>/`.
4. **BRD and other documents.** Ask explicitly: is there a BRD (or SRS, functional spec)? Ask the user to put it in the docs folder as PDF or DOCX. Also ask for: the project plan or sprint plan, existing gap or question lists (from a team lead or BA), designs or mockups, API specs or Swagger, and the names of external systems.
5. **Confirm before moving on.** Summarize what you have and what is missing, then ask "Is that everything, or should I wait for more?" Proceed only when the user confirms or says to go ahead without the rest. Record what is missing; it lowers confidence later.

Ask in one consolidated message where possible (use `AskUserQuestion` for choices, plain text for "please place these files"). Don't drip questions one at a time.

## Phase 1: Extract and inventory

Read `references/extraction.md` for commands. Convert everything to text you can quote:
- DOCX: `pandoc -t plain` for prose; `python-docx` for tables (use `scripts/dump_docx_tables.py`). PDF: native read or `pdftotext -layout`.
- Images and mockups: extract from DOCX `word/media/`, map each to its caption.
- Embedded Visio or EMF diagrams: render via the draw.io desktop CLI (`draw.io -x -f png`), also export `.drawio`.
- **Compare the BRD against the stories** table by table (`scripts/compare_docs.py`). If they're identical, say so and only extract what the BRD adds (scope, glossary, permissions, appendices, diagrams). If they differ, the user decides which wins; by default the stories are the latest.

Save extracted BRD content as markdown in `docs/brd/` (overview, roles-and-permissions, use-case-map, process-flow, reference-data, `flows/`, `ui/` with a captioned README). Use relative paths everywhere, never absolute machine paths.

## Phase 2: Quality assessment (be honest)

Read `references/quality-assessment.md` and score the material. Then tell the user the verdict in plain words before building anything:

- **Good:** consistent, rules and data tables defined, few gaps. Say so; the primer will be reliable.
- **Mixed:** usable, but name the weak areas.
- **Poor:** contradictory, vague, missing data definitions, undefined terms everywhere. Say it explicitly: *"The business material is poor. A lot of points need clarification and resolution from the business, and the artifact cannot be very reliable at this stage. It can only be used as a starting point to categorize the business visually so you can check it quickly."* Do not soften this. Put the same warning as a visible banner at the top of the artifact, and repeat the confidence level in the Open points tab.

Being honest here matters more than looking helpful: people will build on what the primer says.

## Phase 3: Gap analysis

While reading, log every inconsistency, contradiction, undefined term, field with no source, missing appendix. Rules that make the gap list trustworthy:

- **Quote the source.** Every gap cites the rule or table ID (for example "UC001 BR013", "table 001-04") and, when the wording matters, the exact text (keep original language, for example Arabic).
- **Separate what is written from what is implied from what you assume.** "Required by the business", "implied by the field definition", "our assumption" are different things; label them. Never present an assumption as a requirement.
- **Classify each item**: business question (for the BA), project-management concern (plan, sprints, estimates: for the team lead), or technical decision (retry counts, storage, algorithms: for the dev team, not a business question).
- **Check before flagging.** Diagrams are usually simplified main-path overviews; don't call a missing alternative path a contradiction. Re-read the source before claiming a field is missing or two rules disagree.
- **Mark general knowledge.** If you add something not in the documents (a national VAT rate, what a standard scale means, what an external platform is), say it comes from general knowledge.

Write the outputs (see `references/gap-files.md` for formats):
- `analysis-notes.md`: internal scope, decisions, working assumptions.
- `business-questions.md`: shareable with the business: hedged wording ("we are assuming"), no file paths, no em dashes, one section per story.
- `brd-context-and-business-gaps.md`: gap table, open items, change log.

If the repo has a `sprint-planning` skill, put these in its sprint folder; otherwise use `docs/business/`.

## Phase 4: Build the onboarding artifact

**The tabs follow the business, not a template.** Every project gets a small core; everything else is chosen from what *this* business actually depends on. A project built around partner integrations needs an Integrations tab and a system map. A back-office tool with ten screens and no integrations needs a Screens tab instead. A pricing engine needs a Calculations tab. Read `references/artifact-tabs.md` for the core tabs, the catalog of optional tabs, and the signals for each.

1. **Plan the tabs from evidence.** Count what dominates the material: integrations and data tables, screens and mockups, calculations, approval workflows, scheduled jobs, reports, roles, regulations. Pick the tabs a developer needs to understand *this* business, merge thin topics into another tab, and drop tabs that would be nearly empty.
2. **Propose the plan before building.** Show the tab list with one line each on why it's there (with the evidence, for example "24 API data tables, 4 external systems"), and what you left out and why. Let the user adjust.
3. **Build** after the user agrees. Load the artifact design guidance (Artifact quickstart) first. Write for a newcomer: plain words, active voice, real examples from the material. Cross-link tabs to the Extra clarifications sections with small "more ↗" links. Publish it as an artifact and give the link.

The tab plan can change later: when the user's questions keep landing on one topic, suggest promoting it to its own tab.

## Phase 5: Iterate with the user

The user will ask questions ("what is X?", "why can't Y call Z directly?", "is this a valid question?"). For each:
- Answer from the sources, quoting the rule ID and text. Say clearly when the documents don't answer it.
- If the answer reveals a new gap, log it (Phase 3 rules) and say where you logged it.
- Offer to add the answer to the Extra clarifications tab in the right group, with "more ↗" links from related tabs.

Typical follow-up deliverables the user may ask for (see `references/deliverables.md`): a business-gaps document in a team-lead format (markdown plus a styled PDF with clickable story links and brief source quotes), a simplified one-line-per-question version, an integrations Excel sheet with dropdowns, and a `/project-context` command so any new AI session can reload this context.

## Principles

- Inputs first, analysis second, artifact third.
- Every claim traces to a source ID; quotes stay in the original language.
- Honest confidence. Poor material gets a poor-material warning, in chat and in the artifact.
- Written vs implied vs assumed, always labelled.
- Business questions vs PM concerns vs tech decisions, never mixed.
- Relative paths only.

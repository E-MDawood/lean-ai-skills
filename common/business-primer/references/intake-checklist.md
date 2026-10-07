# Intake checklist (Phase 0)

Run this before any analysis. The goal is one consolidated request to the user, then a confirmation that nothing else is coming.

## 1. What did the user give you?

Classify what arrived:

| Have | Then ask for |
|---|---|
| Nothing | The user stories (Jira links or keys, or exported files). Stop until they arrive. |
| Jira links or keys only | Fetch them (section 2). Then ask for the BRD, attachments and the other items in section 4. |
| Story files only (docx, pdf) | Ask whether there are Jira keys (for sub-tasks and comments), whether a BRD exists, and whether the files have attachments not yet placed. |
| A BRD only | Ask for the user stories: they are usually the latest version, and the BRD may be older. |
| Stories and a BRD | Ask for attachments, plan, existing gap lists, designs, API specs. |

## 2. Reading Jira properly

For every story key, collect the whole record, not just the description:

- `getJiraIssue` with `fields: ["*all"]`, `responseContentFormat: "markdown"`, `expand: "renderedFields"`: description, acceptance criteria, labels, priority, status, reporter, **comments**, **attachment list**, **issue links**.
- Sub-tasks: `searchJiraIssuesUsingJql` with `parent = KEY` (and `parent in (KEY1, KEY2)` for many).
- Linked issues: follow `issuelinks` (blocks, relates to, duplicates, test cases) and fetch the important ones.
- Remote links: `getJiraIssueRemoteIssueLinks` (Confluence pages, external specs).
- Epics: if the stories share an epic, fetch the epic description; it often holds scope.

Treat unanswered comments ("@BA what does X mean?") as raw evidence of gaps; they go into the gap analysis later.

If the connector errors (for example `403 The app is not installed on this instance`, or auth missing):
- Tell the user exactly what failed and that the fix is on their side (install or approve the app, or reconnect the connector).
- Offer the fallback: export the stories, sub-tasks and comments, or paste them.
- Never silently continue on descriptions alone.

## 3. Attachments

You cannot download Jira attachments. For each story, list the attachment file names you saw in the record and ask the user to place them in `docs/stories/<STORY-KEY>/`. Ask the same for attachments of sub-tasks.

## 4. Other material to request

Ask once, as a checklist:
- **BRD / SRS / functional spec.** "If there is one, please place it in the docs folder as PDF or DOCX."
- **Appendices** the stories refer to (status lists, code lists, role matrix, SLAs, numbering, attachment rules).
- **Project or sprint plan** (which stories in which sprint, dates).
- **Existing question or gap lists** from a team lead, BA or backend team (merge, don't duplicate).
- **Designs or mockups** (Figma links, screenshots) → `docs/designs/` or the story folder.
- **API specs / Swagger / integration guides** for the systems involved.
- **Names and owners of external systems** mentioned in the stories.
- **Language preference** for the outputs (for example English with Arabic labels).

## 5. Confirm and record

Summarize: what you have (with counts), what is missing, what you could not read and why. Ask: "Is that everything, or should I wait for more?" Proceed on confirmation, or when the user says to go ahead without the missing items. Write the missing items into the gaps file and carry them into the quality assessment, since each missing input lowers confidence.

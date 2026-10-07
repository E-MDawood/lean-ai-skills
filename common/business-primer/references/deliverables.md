# Follow-up deliverables (on request)

## Business gaps document (full)
- Markdown, in the team lead's format if one exists: ID (BA-01…), sprint or priority, due date, references, the question, "Why it matters", "Until answered".
- After the ID line, the stories as clickable links: `([KEY](https://<site>.atlassian.net/browse/KEY), UC_xxx)`; several stories separated by semicolons.
- A brief source quote only where the question is about specific wording (one line, original language).
- Merge related questions into one; remove what the user marks as answered; renumber and fix internal references.

## Styled PDF
- Render the markdown to HTML and print with headless Chrome (`--headless=new --no-pdf-header-footer --print-to-pdf=...`). Match the reference document's fonts, colours and layout by rendering its pages (`pdftoppm`) and sampling colours.
- Keep Jira links clickable (check with `pdfinfo -url`). Set Arabic quotes right-to-left in an Arabic-capable font.
- Avoid orphaned headings (start a section on a new page if needed).

## Simplified version
- Same questions, one paragraph each: the question with any needed reference woven in, ending with `(KEY, UC_xxx)`. No sprints, dates, "why" or "until". Saved with a `-simplified` suffix unless the user names it.

## Integrations Excel
- One row per integration; bilingual headers "Arabic / English" when the business is Arabic; dropdowns with colour-coded conditional formatting for enumerated columns; clickable story links; a Notes sheet explaining each column's rules. Ask before adding rows that the Integrations tab does not list.

## `/project-context` command
- `.claude/commands/project-context.md`: tells a fresh session which files to read in order, to report the current phase and open questions, and the standing rules (gap logging, writing style, relative paths, Jira fallback).

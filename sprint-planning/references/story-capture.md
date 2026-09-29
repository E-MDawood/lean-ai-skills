# Phase 2 reference — Story capture → `stories.md`

## Purpose

`stories.md` is the raw source of truth for what Jira actually says — nothing else. Every other phase's file (`analysis-notes.md`, `business-questions.md`, the dev plan) references it rather than repeating it, so it has to be complete and untouched by interpretation. If `analysis-notes.md` or `business-questions.md` ever start accumulating scope notes or commentary inline, that's a sign they've drifted back into this file's job — split them back out.

## Fetching

- Use `mcp__atlassian__getJiraIssue` per ticket, with `fields: ["*all"]` and `responseContentFormat: "markdown"`, resolving the cloud ID from the site hostname first (pass the hostname as `cloudId` directly; only call `getAccessibleAtlassianResources` if that fails).
- Fetch stories in parallel (multiple tool calls in one message) — there's no ordering dependency between them.
- If a fetch fails for a story, don't skip it silently: note the failure to the user and ask them to paste the description manually.
- Capture, per story: title, Jira key, labels, priority, reporter, full description (including any embedded tables/parameters), acceptance criteria, related/linked test tickets, and any unresolved Jira comments on the ticket itself (e.g. someone asking the reporter for clarification) — that's part of the raw record, not analysis.

## Writing the file

- One `##` section per story, ordered however the stories were given (Jira key first in the heading, e.g. `## REDJ-463 - Receive and Display External Referral for TPA`).
- Preserve the story's own structure (numbered lists, tables, sub-headings) as given — don't paraphrase or summarize.
- **Zero added commentary.** No "Scope note," no cross-story remarks, no flags like "this seems to conflict with story X." Every one of those belongs in `analysis-notes.md` (Phase 3) instead. If you notice something worth flagging while capturing a story, hold onto it and raise it in Phase 3, don't drop it into this file to avoid losing the thought.
- Add a short intro paragraph at the top: what sprint this is, where it's tracked in Jira, and pointers to the sibling files (`analysis-notes.md` for judgment/decisions, `business-questions.md` for open items) — but keep even this intro free of any actual analysis content, it's just navigation.

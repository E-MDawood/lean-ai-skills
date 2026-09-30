---
name: estimation
description: >
  Use this skill whenever the user wants to estimate time for user stories,
  generate a sprint time estimation Excel file, or plan how long Jira stories
  will take. Trigger when the user provides Jira links and asks for estimates,
  says "estimate these stories", "sprint estimation", "how long will this take",
  "time planning", or pastes ticket IDs in a planning context - even if they
  don't explicitly say "estimation". Also trigger when the user asks to fill an
  estimation spreadsheet.
---

# Sprint Time Estimation Skill

This skill takes a set of Jira user story links, explores the codebase to understand scope, and generates a fully-filled Sprint Time Estimation Excel file (`docs/estimations/<filename>.xlsx`).

---

## Step 1 - Detect repo type

Detect whether the current repo is frontend or backend by checking:
- Directory structure (e.g., `src/`, `package.json`, `tsconfig.json` = frontend; `src/main`, `go.mod`, `pom.xml` = backend)
- File patterns and frameworks in use
- Jira project or ticket context if available

---

## Step 2 - Collect required inputs (ask once, upfront)

Ask for the following if not already provided:

1. **Jira story links or ticket IDs** (required) - e.g. `REDJ-464, REDJ-593`
2. **Sprint number** (optional) - only affects the output file name
3. **Estimation scope** (required) - Based on detected repo type, ask:
   - If frontend repo detected: Do you want estimates for **this frontend repo only**, or **both frontend and backend?**
   - If backend repo detected: Do you want estimates for **this backend repo only**, or **both frontend and backend?**
   
   If the user chooses "both", ask a follow-up: *Would you like to provide the local path to the [backend/frontend] repo for more accurate estimates? (This will give us access to both sides and improve accuracy.)*
   
   If the user provides a path, use it for context when estimating that side. If not, proceed with estimates for both sides with a note that accuracy will be lower.

   **"Both" means one combined sheet, not two.** When estimating both frontend and backend, produce a single estimation sheet with one row per story. Internally assess the effort for the frontend side and the backend side separately, then use the higher of the two as that story's estimation. Never split this into separate frontend/backend rows or sheets, and never state in the justification which side (frontend/backend) drove the estimate or that one side took more effort than the other - that's an implementation detail PMs and BAs don't need. The justification should read the same as if only one side existed for the story.

If the user didn't provide all three in their first message, ask for them together in a single message. Don't ask separately.

**File naming rules:**
- With sprint number: `Sprint <N> Time Estimation.xlsx`
- Without sprint number: `Time Estimation for REDJ-XXX, REDJ-YYY.xlsx`
  - List up to 3 ticket IDs; if more than 3, append `et al.` after the third

**Output directory: always `docs/estimations/` - never ask the user where to save.**

---

## Step 3 - Fetch story details via Atlassian MCP

For each ticket, call `mcp__atlassian__getJiraIssue` to retrieve:
- Summary (story title)
- Description
- Acceptance criteria
- Story type
- Linked issues (for dependencies)
- Labels

If MCP fetch fails for a story, note it in the final report and ask the user to paste the story description manually. Do not skip the story.

---

## Step 4 - Explore the codebase

For each story, use the title and description to guide targeted searches across the repo. Assess:

- Whether similar work already exists (lowers estimate)
- Integration points: APIs, services, state management, shared components
- Areas with unclear scope or missing context (raises estimate)

Use Explore agents for broad searches; read specific files for deeper context. Stay focused on what the stories actually touch - don't scan the whole codebase.

---

## Step 5 - Determine dependencies and execution order

Cross-reference Jira linked issues with code structure to assign:

- **Dependencies** - comma-separated ticket IDs of stories that must complete first
- **Execution Order** - integer (1 = first). Ties are allowed: stories with the same number are co-dependent and can run in parallel.

---

## Step 6 - Estimate each story

For each story, produce all 7 columns:

| Column | What to fill |
|---|---|
| Execution Order | Integer; ties allowed for parallel work |
| Story # | Jira ticket ID, clickable link |
| Story Name | Full story title, clickable link |
| Dependencies | Comma-separated ticket IDs of blockers (blank if none). A single dependency becomes a clickable link in the Excel file; multiple stay as plain text (Excel limitation). |
| Estimation (in hours) | Use the complexity table below |
| Justification | Brief explanation of the estimate (1-2 sentences), written entirely for a business/PM audience - never technical. Frame drivers in terms a BA or PM cares about: how much of the story is new work, how many workflows/screens/user-facing pieces are involved, how clear or unclear the requirements are, how many teams or approvals are involved, whether it depends on things outside our control. Never mention code-level detail: no component/API/endpoint/schema names, no "frontend vs backend", no library or framework names, no file counts. Think "what would I tell a PM in a status meeting", not "what would I tell an engineer in a PR". |
| Reduction Tips | Only include if there's a genuine, business-level way to reduce effort. Good tips: splitting the story into smaller stories (e.g., ship a core slice now, defer the rest), implementing only a subset of the story now rather than the full scope, asking for more/clearer business detail on an ambiguous requirement, proposing a simpler business approach to achieve the same goal. Never suggest technical reuse (e.g., "reuse an existing component/structure/pattern") - that is not a valid reduction tip for this column. Leave blank whenever no genuine, realistic reduction tip exists - a blank cell is always better than a tip that doesn't reflect reality. |

**Complexity reference table:**

| Complexity | Hours |
|---|---|
| Trivial - config, label, 1-2 files changed | 2-4 |
| Small - single component or endpoint | 4-8 |
| Medium - multi-component, some integration | 8-20 |
| Large - full feature, cross-team, unknowns | 20-40 |
| Epic - architectural or very unclear scope | 40+ |

**Estimation guidance:**
- Bias lower when similar code already exists in the repo
- Bias higher when scope is unclear or involves external integrations
- This is a pre-planning stage - estimates don't need to be exact, but must be reasoned

**Clarifying questions:** Ask targeted questions when scope is ambiguous - one focused question per story is better than five broad ones. Don't ask for information you can find in the code or Jira.

---

## Step 7 - Generate the Excel file

Write the story data to a JSON file, then run the bundled script:

```bash
python .claude/skills/estimation/scripts/generate_excel.py \
  --data /tmp/estimation_data.json \
  --output "docs/estimations/<filename>.xlsx" \
  --skill-dir ".claude/skills/estimation"
```

**JSON input schema:**
```json
{
  "jira_base_url": "https://leansa.atlassian.net/browse/",
  "stories": [
    {
      "ticket": "REDJ-464",
      "name": "Story name",
      "url": "https://leansa.atlassian.net/browse/REDJ-464",
      "execution_order": 1,
      "dependencies": "REDJ-463",
      "estimation_hours": 8,
      "justification": "Business/PM-friendly reason, no technical detail",
      "reduction_tips": "Business-level tip (e.g. split into smaller stories, implement a subset now, get more business detail), or null if no genuine reduction exists"
    }
  ]
}
```

`jira_base_url` defaults to `https://leansa.atlassian.net/browse/` if omitted. Set `reduction_tips` to `null` or omit it entirely when there is no genuine reduction opportunity - do not fill it with generic advice just to have something in the cell.

The script loads `assets/template.xlsx`, clears the data rows, writes new story rows with the same formatting, updates the Summary sheet formulas to match the new row count, and saves to the output path. The Column Guide tab is left untouched.

---

## Step 8 - Report

After saving, report:

1. The output file path
2. Total hours and equivalent days (at 8h/day)
3. Any stories that had ambiguous scope or need team review (flag them explicitly)
4. Any stories where MCP fetch failed or data was incomplete

---
name: deployment-doc
description: Generates the official Lean deployment document (Product Release Specification .docx) for staging and production deployments. Auto-detects migration scripts, env vars, Jira tickets, and sprint plans — then collects remaining info from the developer before producing the Word file.
whenToUse: Activate when the user says "create deployment doc", "generate deployment document", "prepare release doc", "deployment document for sprint", or any variation. Also activate at the end of a sprint when the developer needs to send a delivery package to the project manager.
---

# Deployment Document Generator

> You are generating the official **Product Release Specification** Word document (.docx) that gets sent to the project manager for staging and production deployments.
> The developer does NOT have access to deploy to staging/production — this document is the handoff package.
> Output must be a `.docx` file. Never produce markdown or PDF.

---

## Folder Structure Reference

```
docs/
├── api/
│   └── swagger.json
├── estimation/
│   └── sprint-<N>-estimation.md
├── designs/           ← frontend only, .gitignored
├── stories/           ← folders named by story number (e.g. PATJ-42/, PATJ-43/)
├── diagrams/          ← backend
└── plans/
    ├── README.md
    └── sprint-<N>/
        ├── backend-api-changes.md
        ├── frontend-api-changes.md
        ├── stories-plan.md
        ├── api-changes-inconsistencies.md
        └── deployment-requirements.md    ← env vars, DNS, integrations for this sprint

docs/delivery/
├── README.md
├── HLD/
├── deployment-documents/                 ← OUTPUT: .docx goes here
└── scripts/
    ├── schema-migrations/                ← EF Core SQL scripts (.sql)
    └── data-migrations/                  ← manual data scripts (.sql)
```

If `docs/delivery/` or any subfolder does not exist, create it before proceeding.

---

## Phase 1 — Ask Sprint Number First

Before any auto-detection, ask one question:

```
What is the sprint number for this deployment?
```

This is needed to find `docs/plans/sprint-{N}/deployment-requirements.md` and to name the output file.

---

## Phase 2 — Auto-Detect (run silently after getting sprint number)

### 2a. Deployment requirements
- Read `docs/plans/sprint-{N}/deployment-requirements.md`
- Extract: new environment variables, DNS entries, new integrations, deployment notes
- If the file does not exist: note it as missing, will ask developer

### 2b. DB scripts
- List all `.sql` files in `docs/delivery/scripts/schema-migrations/`
- List all `.sql` files in `docs/delivery/scripts/data-migrations/`
- If no files found: note that scripts may need to be generated (see Phase 3)

### 2c. EF Core migrations
- Read all files in `Migrations/` folder
- List migration names in chronological order (filename prefix = timestamp)
- Last migration = most recent = "to" target for script generation
- Note if any migration has no corresponding `.sql` in schema-migrations

### 2d. Jira tickets — always ask the developer for the board URL

Always ask for the sprint board URL — never assume MCP or git log results represent the correct scope.
The developer decides what is in scope; not every ticket assigned to them belongs to this release and vice versa.

Use MCP / git log / stories folder only as **reference hints** to show alongside the question — not as the final answer.

If Atlassian MCP is available, fetch candidates silently and present them as suggestions:
```
mcp__atlassian__searchJiraIssuesUsingJql
JQL: issueKey in (extracted-keys) ORDER BY created ASC
```
Show the suggestions but always require the developer to confirm or provide the correct board URL.

### 2e. Project name and version
- Read `.csproj` — use `<AssemblyName>` or filename as project name
- Read `<Version>` tag if present
- Read `appsettings.json` for any version hints

---

## Phase 3 — Collect Remaining Info (interactive questions)

Ask questions in two rounds. Use `AskUserQuestion` for choice-based questions. Ask free-text questions (URLs, tag values, env var keys) directly in chat — never use "notes field" for these.

### Round A — Use AskUserQuestion (choice-based, up to 4 at a time)

Ask these together in one AskUserQuestion call:

1. **Release version** — options: `1.0.0`, `1.0.1`, `1.1.0`, `Other (type in chat)`
2. **Frontend tag** — options: `N/A — backend only`, `Same as backend`, `Other (type in chat)`
3. **Jira scope** — options: `Board URL (I'll ask in chat)`, `Use {candidates} from git`, `Other (type in chat)`
4. **New env vars?** — options: `None`, `Yes (I'll provide in chat)`
5. **DNS / Integrations?** — options: `None`, `New DNS (type in chat)`, `New integration (type in chat)`, `Both (type in chat)`
6. **DB script name** — options: `Sprint{N}-{YYYY-MM-DD}.sql`, `Other (type in chat)`

### Round B — Ask in chat (free-text, one message)

After Round A, ask in a single chat message for everything that needs free text:

```
Please provide the following (reply with each value on a new line):

Backend tag   : (e.g. 0.0.20)
[Board URL    : paste Jira sprint board URL]      ← only if "Board URL" was chosen
[Frontend tag : type the exact tag]               ← only if "Other" was chosen
[Env vars     : KEY=value, one per line]          ← only if "Yes" was chosen
[DNS          : the DNS entry]                    ← only if DNS was chosen
[Integration  : the service name]                 ← only if Integration was chosen
[Script name  : your preferred file name]         ← only if "Other" was chosen
```

Only include lines that are actually needed based on Round A answers.
Wait for the developer's reply before proceeding to Phase 4.

---

## Phase 4 — Generate Migration Script (if needed)

If new EF Core migrations exist but no `.sql` file is in `docs/delivery/scripts/schema-migrations/`:

```powershell
# Create folder if missing
New-Item -ItemType Directory -Force "docs\delivery\scripts\schema-migrations"

# Generate migration script
dotnet ef migrations script {FromMigration} -o "docs\delivery\scripts\schema-migrations\Sprint{N}-{YYYY-MM-DD}.sql"
```

- `{FromMigration}` = last deployed migration name. Use `0` if this is the first deployment (generates full schema).
- For rollback script: save as `Sprint{N}-{YYYY-MM-DD}-rollback.sql` in the same folder.
- Tell the developer: **"Please verify the generated SQL file before I continue."**

If the developer provides a script file name that already exists in the folder, use it as-is — do not regenerate.

---

## Phase 5 — Generate the Word Document

### Output file name
```
docs/delivery/deployment-documents/{ProjectName}-Sprint{N}-Deploy-{YYYY-MM-DD}.docx
```
- `{ProjectName}` = the project name detected from `.csproj` (e.g. `IADataEnquiry`)
- `{N}` = sprint number
- `{YYYY-MM-DD}` = today's date

Example: `IADataEnquiry-Sprint1-Deploy-2026-06-22.docx`

---

### Template and logo

Before generating, check in this order:

1. **Template file** — look for `docs/delivery/lean-template.docx`
   - If found: use it as the base document (copy it, then fill in the content sections)
   - If not found: generate from scratch using the structure below

2. **Logo image** — look for `docs/delivery/lean-logo.png` (or `.jpg`, `.svg`)
   - If found: embed it on the cover page at top-left, sized ~3cm wide
   - If not found: **ask the developer** to place the logo file in `docs/delivery/` before continuing — do NOT use a placeholder box

---

### Word generation

Use `python-docx` (Python) to generate the file — it is available without any additional skill.

The `docx` skill (if available in this session) provides detailed API reference and makes generation more reliable, but it is **not required**. The skill works fully without it.

Generate using a Python script written to the scratchpad directory, then run it with `python`.

The document must match the official Lean **Product Release Specification** template exactly.

---

### Cover Page
- Lean logo top-left — embed from `docs/delivery/lean-logo.png` if it exists; otherwise leave a white placeholder box of similar size
- Large bold title: **Product Release Specification**
- Footer: `www.lean.sa` — left aligned
- Decorative horizontal lines bottom-right corner (Lean brand style)

---

### Page 2 onward

**Document header table** (2 columns, no visible heading — first thing on page 2):

| **Project** | {ProjectName} |
|---|---|
| **Version** | Release {Version} |

---

#### 1- Scope

| **Link** |
|---|
| {JiraSprintBoardURL or individual ticket URLs} |

*One row per Jira ticket or sprint board link. If only a board URL is available, use one row.*

---

#### 2- Tags

| **Application** | **Version** |
|---|---|
| Backend | {BackendTag} |
| Frontend | {FrontendTag} |

*Omit the Frontend row entirely if N/A.*

---

#### 3- DNS

| **No.** | **DNS** |
|---|---|
| *(leave row empty if none)* | |

*If new DNS entries exist, list one per row with incrementing No.*

---

#### 4- Integration Required

| **No.** | **Service** |
|---|---|
| *(leave row empty if none)* | |

*If new integrations exist, list one per row.*

---

#### 5- DB Scripts

| **No.** | **File Name** |
|---|---|
| 1 | {script-file-name}.sql |

*One row per .sql file (schema-migrations first, then data-migrations). Leave empty rows if no scripts.*

---

#### 6- Environment Variables

| **Key** | **Value** | **Status** |
|---|---|---|
| {KEY_NAME} | {value} | *(PM fills Status)* |

*Include ONLY new or changed variables for this sprint — not all existing env vars.*
*Leave this section with empty rows if no new env vars.*

---

#### 7- Deployment Plan

| **No.** | **Task** | **Owner** |
|---|---|---|
| 1 | Run migration script | DB admin |
| 2 | Deploy application | Deployment admin |

*Add extra rows only if deployment-requirements.md specifies additional steps.*
*If no DB scripts: remove row 1.*

---

#### 8- Rollback Plan

| **No.** | **Task** | **Owner** |
|---|---|---|
| 1 | Run the file Sprint{N}-{YYYY-MM-DD}-rollback.sql | DB admin |
| 2 | Restore the past version of deployment | Deployment admin |

*If no DB scripts: remove row 1.*

---

## Document Formatting Rules

| Property | Value |
|---|---|
| Font | Calibri |
| Body size | 11pt |
| Section heading size | 13pt bold |
| Section heading color | `#1D3557` (Lean dark navy blue) |
| Table header rows | Bold |
| Table borders | Visible, all cells |
| Page header (page 2+) | Left: `Lean Business Services` — Right: `Deployment Document` |
| Page footer | Left: `Lean Business Services` — Right: `Page No.` with auto page number |
| Cover page | No header/footer except `www.lean.sa` at bottom left |

---

## Edge Cases

| Situation | Behavior |
|---|---|
| No migrations exist | Skip DB Scripts section rows, remove DB steps from Deployment and Rollback plans |
| Script file already exists in schema-migrations/ | Use existing file, do not regenerate |
| No deployment-requirements.md | Ask developer for env vars, DNS, integrations directly |
| No stories/ folder or MCP unavailable | Ask for sprint board URL or ticket list |
| Frontend tag = N/A | Omit Frontend row from Tags table entirely |
| First deployment (no prior migration) | Use `0` as FromMigration in script command |
| Multiple schema script files | List all in DB Scripts table, numbered sequentially |

---

## Output Checklist

Before saving:
- [ ] File saved to `docs/delivery/deployment-documents/{ProjectName}-Sprint{N}-Deploy-{YYYY-MM-DD}.docx`
- [ ] All 8 sections present
- [ ] Cover page has Lean branding
- [ ] Backend tag and Frontend tag filled (most critical fields)
- [ ] DB Scripts lists all `.sql` files from `docs/delivery/scripts/`
- [ ] Env vars section has only NEW/CHANGED keys for this sprint
- [ ] Rollback plan references the correct rollback SQL file name
- [ ] Page headers and footers match the template on all pages after the cover
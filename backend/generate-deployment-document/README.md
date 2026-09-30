# deployment-doc Skill

Generates the official **Lean Product Release Specification** Word document (`.docx`) used to hand off a sprint release to the project manager for staging and production deployment.

The development team does not have direct access to staging/production environments — this document is the formal delivery package sent to the PM.

---

## How to Use

Type this in any Claude Code session inside the repo:

```
/deployment-doc
```

Claude will:
1. Ask for the sprint number
2. Auto-detect everything it can from the repo
3. Ask one consolidated set of questions for what it could not detect
4. Generate the migration SQL script if needed
5. Produce the `.docx` file in `docs/delivery/deployment-documents/`

---

## What It Auto-Detects

| What | Where it looks |
|---|---|
| Project name | `.csproj` filename |
| New env vars & deployment notes | `docs/plans/sprint-{N}/deployment-requirements.md` |
| DB migration scripts | `docs/delivery/scripts/schema-migrations/` |
| Data scripts | `docs/delivery/scripts/data-migrations/` |
| EF Core migrations | `Migrations/` folder |
| Jira tickets | Atlassian MCP → `docs/stories/` folders → git log |

---

## What It Will Ask You

After auto-detection, Claude asks one set of questions — all at once:

| Field | Notes |
|---|---|
| Release version | e.g. `1.0.0` |
| Backend tag | ⚠ Required — e.g. `0.0.282` |
| Frontend tag | ⚠ Required — enter `N/A` if backend-only |
| Jira sprint board URL | Only if MCP and stories folder are unavailable |
| DB script name | Only if not found in the scripts folder |
| New env vars | Only if `deployment-requirements.md` is missing |
| New DNS / integrations | Confirm or provide |

---

## Output

```
docs/delivery/deployment-documents/{ProjectName}-Sprint{N}-Deploy-{YYYY-MM-DD}.docx
```

Example: `IADataEnquiry-Sprint1-Deploy-2026-06-22.docx`

The document follows the official Lean template with 8 sections:

1. **Scope** — Jira sprint board / ticket links
2. **Tags** — Backend and Frontend version tags
3. **DNS** — New DNS entries (if any)
4. **Integration Required** — New service integrations (if any)
5. **DB Scripts** — SQL files to run during deployment
6. **Environment Variables** — New or changed env vars only
7. **Deployment Plan** — Ordered tasks with owners
8. **Rollback Plan** — Steps to revert if deployment fails

---

## DB Migration Script Generation

If new EF Core migrations exist with no corresponding SQL script, the skill runs:

```powershell
dotnet ef migrations script {FromMigration} -o "docs\delivery\scripts\schema-migrations\Sprint{N}-{YYYY-MM-DD}.sql"
```

- For the **first deployment**: uses `0` as the from-migration (full schema from scratch)
- For **subsequent deployments**: uses the last deployed migration name as the starting point
- A rollback file is also generated: `Sprint{N}-{YYYY-MM-DD}-rollback.sql`

Always verify the generated `.sql` before sending the document.

---

## Folder Structure

```
docs/delivery/
├── deployment-documents/     ← generated .docx files go here
└── scripts/
    ├── schema-migrations/    ← EF Core SQL scripts
    └── data-migrations/      ← manual data seed/update scripts

docs/plans/
└── sprint-{N}/
    └── deployment-requirements.md   ← env vars, DNS, integrations for this sprint
```

---

## Skill Files

```
.claude/skills/deployment-doc/
├── SKILL.md      ← skill instructions (Claude reads this)
└── README.md     ← this file
```

---

## Template and Logo Setup

Place these files in `docs/delivery/` before running the skill:

| File | Purpose |
|---|---|
| `lean-template.docx` | Base Word template with Lean branding — skill uses it as the starting document |
| `lean-logo.png` | Lean logo image — embedded on the cover page top-left |

If neither file exists, the skill will ask you to provide them before generating. Do NOT rely on a placeholder — the logo must be the real Lean logo.

## Notes

- The skill reads `deployment-requirements.md` from the sprint plans folder — keep this file up to date during the sprint so the skill can auto-fill the env vars section
- Backend and Frontend tags are the most critical fields — always confirm them before the document is sent
- The `.docx` is generated using `python-docx` — no extra skill or installation needed, Python is sufficient
- The `docx` skill (if available) provides additional Word API guidance but is **not required** — the skill works without it
- If the Atlassian MCP server is connected in the session, Jira tickets are fetched automatically
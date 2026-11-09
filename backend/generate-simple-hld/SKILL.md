---
name: generate-simple-hld
description: Generate a short, first-time High-Level Design (HLD) covering only integrations, backend, frontend and database, built mainly from the sprint planning docs (produced by the sprint-planning skill), because it's usually written at the start of a sprint before any code exists. Uses existing code, if any, as the baseline. Outputs SimpleHLD.docx with one overview diagram to /docs/delivery/SimpleHLD/. Use when the user asks for a "simple HLD", "first HLD", "initial HLD", "HLD from the planning", "HLD before implementation", or similar. For a full HLD of an implemented system, use `generate-hld` instead.
---

# Generate Simple HLD (first time, planning-based)

A short HLD for the start of a project or sprint, before the code exists. It answers four questions and nothing else:

1. **Integrations:** which external systems we talk to, and how
2. **Backend:** what services/components we're building, on what stack
3. **Frontend:** what the UI is, on what stack
4. **Database:** what database, and what it holds at a high level

The main source is the **planning docs**. Existing code, if there is any, is the baseline the plan builds on. The full, code-derived design document is the `generate-hld` skill's job, so don't grow this one into it: no NuGet tables, no controller route lists, no dependency trees.

## Output bundle

Everything lands in `<backend-project>/docs/delivery/SimpleHLD/`:

- `SimpleHLD.docx`: the deliverable (bordered tables, embedded overview diagram)
- `SimpleHLD.md`: markdown source (regeneration input)
- `diagram-1-overview.drawio` + `.drawio.svg`: the one diagram

The build pipeline is shared with `generate-hld`: call `../generate-hld/templates/regenerate.sh <folder> SimpleHLD` from this skill folder. **Don't copy it into the project.**

---

## Phase 1: Pre-flight

Same as `generate-hld` Phase 1: read `../generate-hld/SKILL.md` § "Phase 1: Pre-flight checks" and follow it. That covers the backend project check (an empty or scaffold-only repo is fine here), the OS check, and tools: `pandoc`, `rsvg-convert`, drawio-desktop, `python3`, `python-docx`. Ask before installing anything.

## Phase 2: Choose the sprint and read the planning

Follow `../generate-hld/references/planning-vs-code.md` §1-§3 and apply **Policy B (planning first)**:

- Find the planning docs. If there are none, ask where they are (reference §1.3). If the user says there are none, stop and suggest `generate-hld` instead. A planning-based HLD with no planning isn't possible, and this skill must not make the design up.
- Sprint: reuse it if the conversation already established it. Otherwise use the latest sprint folder and state it in the plan (Phase 4).
- Read the plan files for sprints ≤ N and extract only what the four sections need (see Phase 5).

## Phase 3: Baseline from the code (light)

Only if there is real code. Read just enough to keep the document from contradicting what already exists:

- Backend: `*.csproj` (target framework, the main packages that show stack choices: EF Core/Dapper, Hangfire, Kafka, auth), `Program.cs` wiring, top-level folders
- Database: provider (SQL Server / PostgreSQL / …), `DbContext` names, and whether migrations or `.sql` scripts are the schema source
- Integrations: `HttpClient` registrations and integration service classes
- Frontend: ask with `AskUserQuestion`, "Where is the frontend for this backend?" Options: "I have the path" (read `package.json` only) / "It's described in the planning" / "No frontend". Never explore the frontend beyond `package.json`.

If code and plan disagree about something that already exists, the code wins. Mention the disagreement in the end-of-run summary.

## Phase 4: Plan (in the chat, before writing)

Before writing anything, show the user the plan. **Don't enter plan mode** (`EnterPlanMode`): stay in the current mode. Write the plan in the chat as a short message, then go straight on to generating. Don't stop to wait for approval. If the user replies with a correction, apply it and regenerate.

The plan states:

- **Basis:** planning for sprint N (files listed), on top of code at `<sha>` / no code yet
- **Mode:** CREATE, or UPDATE if `SimpleHLD.md` exists. UPDATE rewrites only sections whose content changed, preserves manual edits elsewhere, and warns if the hidden basis comment on the first line names a different sprint.
- **What each of the four sections will say**, in one or two lines each
- **Open points:** things the plan doesn't specify that the document would need (e.g. "integration with NPHIES: transport not specified"). These stay in the chat; they never go in the document.

Then continue to Phase 5.

## Phase 5: Write `SimpleHLD.md`

The document is for other teams, so it describes the whole system and nothing about the build. **Follow `../generate-hld/references/planning-vs-code.md` §6 (What the reader sees).** In short, the document has:
- no basis line, sprint numbers or "generated from the planning / the code"
- no status labels (Existing, Planned, Partial …)
- no open points or open questions
- no references to repos, code files, classes, config, or planning/docs files
- no Jira, use-case or business-rule IDs

Every component, integration and data area is written in the present tense, as part of one system.

Keep it to about 2-4 pages. Put facts in bordered markdown tables (`|---|` separators), with a short sentence of prose above each table. Use this structure:

```markdown
<!-- basis: <hidden basis comment from reference §5> -->
# <System name>: High-Level Design

## 1. Overview
One paragraph: what the system does, for whom, and its main capabilities. Then Figure 1.

![Figure 1: <System> overview](diagram-1-overview.drawio.svg)

## 2. Integrations
| System | Direction | Purpose | Protocol / Mechanism |
(Direction: Inbound / Outbound / Both.)
If none: "No external integrations." (one line, no table)

## 3. Backend
| Component | Responsibility | Technology |
Then a 2-4 row "Key technical choices" table (framework, data access, background processing, auth), with only the rows the code or plan supports.

## 4. Frontend
| Application | Users | Technology |
If "No frontend": "No frontend in scope." (one line)

## 5. Database
| Database | Engine | Purpose |
Then one line per main data area (e.g. "Claims: submitted claims and their responses"). No tables or columns here; that's what `generate-simple-erd` is for.
```

Rules:
- Use the names the plan and code use for things (components, systems, data areas), never file, class or repo names. Don't invent a component, data area, protocol or technology the plan and code don't state. Leave it out and report it in the chat as an open point.
- No sections beyond these five.

## Phase 6: The overview diagram

One drawio diagram, `diagram-1-overview.drawio`. Lay it out as Users → Frontend → Backend (components inside one container) → Database, with external systems on the right, one labelled edge each (protocol). Draw every box the same way, built or planned: no dashed borders, no status legend. Name boxes by what they are, not by repo or project name.

Before writing XML, read `../generate-hld/templates/example-diagram-3-dependency-mapping.drawio` and reuse its `mxGraphModel` structure and colour palette: blue for client/frontend, green for application, red/pink for data, purple for external services.

**Plain-text labels only.** Use `html=0` and no `whiteSpace=wrap` in every cell style, and break lines with `&#xa;` in the label. With HTML or wrapped labels, drawio exports the text as `foreignObject`: Word and `rsvg-convert` can't render that, and the image gets a "Text is not SVG - cannot display" footer. Route edges so they never cross a box: connect from container edges with `exitX`/`exitY`/`entryX`/`entryY` rather than between inner boxes.

## Phase 7: Build

```bash
bash ../generate-hld/templates/regenerate.sh <backend-project>/docs/delivery/SimpleHLD SimpleHLD
```

(Paths are relative to this skill folder. From the project root, use `.claude/skills/generate-hld/templates/regenerate.sh`.) If a step fails, report the step and its output.

## Phase 8: Verify and report

Check, and print a ✓/✗ table:
- Every row that comes from the plan traces to a line in a sprint ≤ N plan file. Cite the file in the chat, not in the document.
- Every row that comes from the code matches the code.
- Nothing from a sprint after N appears.
- **Reader check:** the `.md` (outside the first-line comment) has none of the items in reference §6. Search it for `Planned`, `Existing`, `sprint`, `Open`, `OD-`, `CL-UC`, `PALJ`, `.cs`, `.md`, `docs/`, `src/` and backticked paths, plus the em dash (U+2014) and en dash (U+2013) in the `.md` and the `.drawio`, and fix any hit.
- The diagram renders in the docx, and its boxes match the tables.

End the chat report with the basis, the open points and any code/plan disagreements, so the user can take them back to the planning.

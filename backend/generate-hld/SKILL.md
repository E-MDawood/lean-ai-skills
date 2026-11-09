---
name: generate-hld
description: Generate or update a High-Level Design (HLD) document for a .NET backend project (with optional React or Next.js frontend). Outputs a Word document with embedded high-resolution diagrams to /docs/delivery/HLD/. Detects existing HLD and updates only the sections whose underlying code has changed. Normally built from the code; when the sprint planning docs (produced by the sprint-planning skill) are ahead of the code, it warns the user and asks whether to build from the code or from the planning, and for which sprint. Use when the user asks to "generate HLD", "create HLD doc", "update HLD", or similar.
---

# Generate HLD Document

Generates a comprehensive High-Level Design document by exploring a .NET backend codebase and a React/Next.js frontend codebase (plus the sprint planning docs when they are ahead of the code), then producing `HLD.docx` with embedded SVG diagrams (with high-res PNG fallbacks) to `<backend-project>/docs/delivery/HLD/`.

## Output bundle

Everything lands in `<backend-project>/docs/delivery/HLD/`:

- `HLD.docx`, the deliverable (with embedded SVG + 4× PNG fallback for each diagram, bordered tables)
- `HLD.md`, markdown source (regeneration input)
- `*.drawio`, editable diagram sources
- `*.drawio.svg`, exported SVG diagrams (referenced by `HLD.md`)

The bash regeneration pipeline lives in this skill at `templates/regenerate.sh` and is called directly from there with the project's HLD folder as its argument. **Do not copy it into the project**.

---

## Phase 1: Pre-flight checks

### 1.1 Confirm this is a backend project

Look for evidence of a backend project at the current working directory. ANY of:
- `*.csproj` and/or `*.sln` (.NET, primary expected case)
- `pom.xml` / `build.gradle` (Java)
- `go.mod` (Go)
- `requirements.txt` / `pyproject.toml` (Python)

If nothing matches, stop and ask the user to confirm they're in the right directory.

### 1.2 Detect operating system

Run `uname -s` once. `Darwin` = macOS, `Linux` = Linux. Use this to pick the right install commands later.

### 1.3 Verify required tools

For each tool below, check it's installed BEFORE you do any work that depends on it. If missing, **explain what it's for** and ask permission to install. Never silently install.

| Tool | What it does | Detection | Install (macOS) | Install (Linux) |
|---|---|---|---|---|
| `pandoc` | Converts the markdown source to .docx | `command -v pandoc` | `brew install pandoc` | `sudo apt-get install -y pandoc` |
| `rsvg-convert` (librsvg) | Renders SVG → high-res PNG fallbacks | `command -v rsvg-convert` | `brew install librsvg` | `sudo apt-get install -y librsvg2-bin` |
| `drawio-desktop` | Exports `.drawio` → `.svg` from CLI | `ls /Applications/draw.io.app/Contents/MacOS/draw.io` (macOS) or `command -v drawio` | `brew install --cask drawio` | (no apt package, see [drawio-desktop releases](https://github.com/jgraph/drawio-desktop/releases)) |
| `python3` | Used by the borders post-processor | `command -v python3` | usually pre-installed | `sudo apt-get install -y python3` |
| `python-docx` | Adds borders to all docx tables | `python3 -c "import docx"` | `pip3 install python-docx --break-system-packages` | `pip3 install python-docx --break-system-packages` |

**Phrasing for the user when something is missing:**
> "I need `<tool>` to `<purpose in one phrase>`. On `<your OS>` I can install it with: `<command>`. Want me to run that?"

---

## Phase 2: Frontend project discovery

Use **AskUserQuestion** to ask:

> "Where is the frontend project for this backend?"

Options:
- **"I have the path"** → user provides absolute path; verify a `package.json` exists there
- **"I'll paste the package.json"** → user pastes contents; document what's inferable but mark project structure / build config as N/A
- **"No frontend"** → skip the UI section entirely

If the user gives a path:
- Verify `package.json` exists. If not, ask again.
- The path can be used to infer Vite vs Next.js, presence of TypeScript, project structure (only if the directory is readable).

---

## Phase 3: Source and mode detection

### 3.1 Source: code or planning

Follow `references/planning-vs-code.md` (in this skill folder) §1-§3 to find the planning docs and compare them with the code, then apply **Policy A (Ask)**:

- **Planning matches the code (or there is no planning)** → source = code. Say so in one line and continue.
- **Planning is ahead of the code** → **stop and warn the user**, then ask, in one `AskUserQuestion` call, (1) whether to generate from the code as built or from the planning, and (2) which sprint. List concrete examples of planned-but-not-built items in the warning so the user can judge.

Do this before mode detection and before the plan in Phase 4; the answer changes what every later phase reads.

When the source is **planning for sprint N**, the HLD describes the system as it will be at the end of sprint N (see §5 of the reference): code as built plus every planned-only item from sprints ≤ N. Record the basis only as the hidden first-line comment from §5. **The document itself follows §6 (What the reader sees):** planned items are written into their sections in the present tense, like everything else. There are no status labels, sprint numbers, open points or references to planning docs in `HLD.md`.

### 3.2 Mode: CREATE vs UPDATE

Check if `<backend-project>/docs/delivery/HLD/HLD.md` exists.

- **Doesn't exist → CREATE mode.** Generate everything from scratch.
- **Exists → UPDATE mode.** Read the current `HLD.md` and plan to diff it section-by-section against what the current code says. Only sections whose source-of-truth has actually changed get rewritten. Manual edits to unchanged sections are preserved.

---

## Phase 4: Plan (in the chat, before writing)

Before generating anything, show the user the plan. **Don't enter plan mode** (`EnterPlanMode`): stay in the current mode. Write the plan in the chat as a short message, then go straight on to generating. Don't stop to wait for approval. If the user replies with a correction, apply it and regenerate.

In the plan, include:
- **Mode:** CREATE or UPDATE
- **Basis:** code at `<sha>`, or planning for sprint N on top of code at `<sha>`, plus the list of planned-only items that will appear in the document, each with its source file
- **Backend stack detected:** e.g., ".NET 8.0, ASP.NET Core, SQL Server (EF Core + Dapper), Hangfire, Kafka, Elastic APM"
- **Frontend stack detected:** e.g., "React 18.2 + Vite 5 + MUI 6" or "Next.js 14 + Tailwind" or "No frontend"
- **Sections that will be generated** (see Phase 6 for the full list and skip rules)
- **Diagrams that will be generated** (see Phase 7)
- **For UPDATE mode:** which sections appear to have changed since last generation (preliminary, confirmed in Phase 6)

Then continue to Phase 5.

---

## Phase 5: Code exploration

Read enough to fill every section honestly. Don't guess.

### Backend (always)

1. **Project file(s):** `*.csproj`, extract `<TargetFramework>` and every `<PackageReference>` with version
2. **Entry point:** `Program.cs` (or `Startup.cs`), see what's wired in (`AddX(...)`, `UseX(...)`)
3. **Folder layout:** top-level dirs (`Controllers/`, `Application/`, `Domain/`, `Infrastructure/`, etc.)
4. **Controllers:** for each `*Controller.cs`, capture class name + `[Route(...)]` value
5. **Service registration / DI:** find `AddScoped<...>`, `AddSingleton<...>`, `AddTransient<...>` to enumerate services
6. **Data access:** `DbContext`, EF Migrations folder, repositories, list entities/tables
7. **External integrations:** `HttpClient` registrations, integration service classes, list each external dependency and its purpose
8. **Background jobs:** Hangfire (`AddHangfire`), Quartz, `BackgroundService` subclasses
9. **Messaging:** Confluent.Kafka, MassTransit, RabbitMQ.Client, Azure.Messaging.*, producers/consumers
10. **Auth:** `AddAuthentication`, JWT config, custom auth handlers/attributes
11. **Monitoring:** Elastic APM, OpenTelemetry, Application Insights, Serilog
12. **Configuration:** `appsettings.json` (if present) for environment names, integration endpoints, etc.

### Frontend (only if path/package.json provided)

1. **`package.json`:** extract React/Next/Vite/Angular versions, all `dependencies` and key `devDependencies`
2. **If full path given:** check `vite.config.*` / `next.config.*` / `tsconfig.json` for build config and TypeScript usage
3. **Folder structure:** `src/` layout (skip if only package.json was given), only meaningful if you can actually read it
4. **Build modes:** look at `scripts` in package.json for multi-environment builds

### Planning (only when the source is planning for sprint N)

Read the plan files for sprints ≤ N listed in `references/planning-vs-code.md` §1 and merge every planned-only item into the matching section: new components into 1.2, new jobs into 1.2.4, new tables into 1.3, new integrations into 1.4, auth changes into 1.5, new queues into 1.6, new config into 1.8, new packages into 2.x **only if the plan names the package**. Don't fill a cell the plan doesn't support, if the plan says "integrate with NPHIES" but not the transport, write what it says and add the gap to the open points you report in the chat at the end, never in the document.

---

## Phase 6: Section selection (dynamic)

Generate ONLY the sections that apply to what you found. Don't pad with "N/A" sections.

Canonical structure (skip rules in **bold**):

| § | Title | Always include? |
|---|---|---|
| 1.1 | Architecture Pattern | **Always** |
| 1.2 | Application Implementation | **Always** (header) |
| 1.2.1 | UI (Frontend) | **Skip if user said "No frontend"** |
| 1.2.2 | Mobile Applications | **Always** ("No mobile applications" if none: a short statement, no table) |
| 1.2.3 | Backend Service | **Always** |
| 1.2.4 | Background Job Processing | **Skip if no Hangfire / Quartz / BackgroundService found** |
| 1.3 | Data Store | **Skip if no database driver found** (rare) |
| 1.4 | External Integrations | **Skip if no external HTTP clients / integration services found** |
| 1.5 | Authentication & Security | **Always** |
| 1.6 | Messaging | **Skip if no messaging client found** (Kafka, RabbitMQ, etc.) |
| 1.7 | Monitoring & Observability | **Always** (even if minimal, e.g., just "Health checks via AspNetCore.HealthChecks") |
| 1.8 | Environment Configuration | **Always** if `appsettings.json` or `IConfiguration` is used |
| 2 | Dependency Mapping | **Always** (header) |
| 2.1 | Backend Dependencies | **Always** (ASCII tree) |
| 2.2 | Frontend Dependencies | **Skip if no frontend** |
| 2.3 | Backend Internal Dependencies | **Always** (NuGet table) |

### Section formatting rules

- All factual content goes into **markdown tables with header row + body rows**.
- Use `|---|---|---|` separators (3+ columns common). Tables get borders applied later.
- Inline code: backticks for file paths, class names, package names.
- Bold for sub-section labels inside a section (e.g., `**Backend Layer Structure:**`).
- Horizontal rule (`---`) between top-level sections only.
- Reference an exemplar at `~/Documents/Work/Lean/Projects/eligibility-backend/docs/delivery/HLD/HLD.md` (your own past output) for tone and depth. **Read it before writing if you have access; it's the gold standard.**

### UPDATE mode: section-by-section diff

For each section in the canonical structure:
1. Generate the new content from the chosen basis: current code, or code + planning for sprint N (in-memory, don't write yet). If the existing `HLD.md` has a different hidden basis comment (e.g. it was built from sprint 5 planning and now you're building from code), tell the user before replacing anything.
2. Locate the matching section in the existing `HLD.md` by header.
3. Normalize whitespace and compare.
4. **If new ≠ existing:** flag for replacement.
5. **If new == existing or section absent in new (e.g., Background Jobs section was added by hand):** leave alone.
6. After all sections processed, replace flagged sections in `HLD.md`. Preserve everything else byte-for-byte where possible.
7. Print a summary: "Updated sections: 1.2.3 (added new package), 1.4 (new integration). Unchanged: ..."

---

## Phase 7: Diagram generation

### 7.1 Which diagrams

Always generate:
- **Diagram 1, Layered Architecture** (the Clean Architecture layers + how requests flow)
- **Diagram 3, Dependency Mapping** (API + every external dep grouped: Data Stores / Messaging / Monitoring / External Services)

Only if relevant:
- **Diagram 2, Background Jobs** (Hangfire/Quartz scheduler + jobs + storage). Skip when no background processing exists. **Renumber accordingly** (then Dependency Mapping becomes Diagram 2).

### 7.2 How to write the .drawio XML

Read the three example files in this skill's `templates/` folder before writing your own:
- `templates/example-diagram-1-layered-architecture.drawio`
- `templates/example-diagram-2-background-jobs.drawio`
- `templates/example-diagram-3-dependency-mapping.drawio`

These are working, importable drawio XML. Adapt them: same `mxGraphModel` structure, same color palette (blue=client/controllers, green=application/messaging, yellow=domain/config, red/pink=infrastructure/data, purple=external services), but with the labels and boxes that match THIS project's actual code.

Save them as `diagram-N-<short-name>.drawio` in the output folder.

### 7.3 Export to SVG

Use the drawio-desktop CLI:
```bash
/Applications/draw.io.app/Contents/MacOS/draw.io \
  --export --format svg --output diagram-1-layered-architecture.drawio.svg \
  diagram-1-layered-architecture.drawio
```

(On Linux, the binary is `drawio` on PATH.)

---

## Phase 8: Generate HLD.md and reference the SVGs

In `HLD.md`, embed each diagram with a markdown image link **placed at the right section** (typically right after the prose that introduces what the diagram shows):

```markdown
![Figure 1a: Backend API Service: Layered Architecture View](diagram-1-layered-architecture.drawio.svg)
```

Use captions like the original template: `Figure Na: <title>`. Numbering follows the diagram numbering chosen in Phase 7.

Standard placement:
- Diagram 1 → after § 1.1 (Architecture Pattern)
- Diagram 2 (Background Jobs, if present) → after § 1.2.4
- Dependency Mapping diagram → at the start of § 2.1

---

## Phase 9: Build .docx + post-process

This is automated by `templates/regenerate.sh` in this skill folder. **Do not copy the script into the project**; call it directly from the template path with the project's HLD folder as its argument:

```bash
bash <skill-folder>/templates/regenerate.sh <backend-project>/docs/delivery/HLD
```

For example, when this skill lives at `<project>/.claude/skills/generate-hld/`:
```bash
bash .claude/skills/generate-hld/templates/regenerate.sh docs/delivery/HLD
```

The script does, in order:
- `.drawio` → `.svg` via drawio-desktop CLI
- 4× resolution PNG renders via `rsvg-convert -z 4`
- `HLD.md` → `HLD.docx` via pandoc
- python-docx pass: add black single-line borders to every cell of every table
- Repackage docx: replace pandoc's low-res PNG fallbacks with the 4× renders (matched by aspect ratio)

If `regenerate.sh` fails on any step, report the exact step and command output to the user.

---

## Phase 10: Verification pass (mandatory)

After generation, verify the document against the actual code. Cross-check at least:

- Every package + version listed matches `*.csproj` / `package.json`
- Every controller route in the table matches a real `[Route(...)]`
- Every external integration named in the integrations section matches a real service class / `HttpClient` registration
- Every section claim (e.g., "Hangfire stores jobs in SQL Server with schema X") matches what `Program.cs` and config say
- All three (or two) embedded diagrams open in the docx and aren't broken images
- **Planning basis only:** every planned-only item in the document traces to a line in a sprint ≤ N plan file, and nothing from a later sprint slipped in. Mark these rows "✓ (plan)" in the summary so they're distinguishable from code-verified rows

Print a verification summary table to the user (✓ for verified items, ✗ + correction needed for any miss).

---

## Tone & quality bar

- **Honesty over completeness.** If you can't determine something (e.g., frontend folder structure when only package.json was provided), say so explicitly; don't invent.
- **The chosen basis is the source of truth.** For code-basis documents, the code; for planning-basis documents, the code for what exists and the plan for what doesn't yet. When in doubt, re-read the file.
- **No long dashes.** Never use the em dash (U+2014) or en dash (U+2013) in `HLD.md` or the diagrams. Use a colon in titles, headings and figure captions, parentheses or a comma in text, and a plain hyphen for ranges (see `references/planning-vs-code.md` §6).
- **No padding.** Don't add architectural framing that isn't supported by the code (e.g., don't claim "microservices" if it's a monolith).
- **The reference exemplar** at `~/Documents/Work/Lean/Projects/eligibility-backend/docs/delivery/HLD/HLD.md` shows the depth, tone, and table density to aim for.

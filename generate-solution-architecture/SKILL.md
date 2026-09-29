---
name: generate-solution-architecture
description: Generate 3 ArchiMate-notation solution architecture diagrams (.drawio + .drawio.svg) plus a database ERD (.dbml) for a .NET backend + React/Next.js frontend solution — Application Landscape, Application Interaction, Data Layer (business roles vs. application services), and an Entity-Relationship Diagram. Outputs standalone files to /docs/delivery/SolutionArchitecture/. Use when the user asks to "generate solution architecture diagrams", "create ArchiMate diagrams", "CNHI solution architecture diagrams", "generate the ERD", or similar.
---

# Generate Solution Architecture Diagrams + ERD

Generates 4 deliverables matching CNHI's Solution Architecture package:
- 3 ArchiMate 3.2-notation diagrams — **Application Landscape**, **Application Interaction**, and **Data Layer** — by exploring a .NET backend codebase (and optional frontend), plus an external business-roles spreadsheet.
- 1 database **ERD**, as a `.dbml` file (for pasting into dbdiagram.io), derived from the backend's actual persisted schema.

Outputs land in `<backend-project>/docs/delivery/SolutionArchitecture/`.

No Word document is produced. This skill is deliberately narrower than `generate-hld`: it never touches pandoc or python-docx. It also never touches a browser — it does not upload, paste, or export anything on dbdiagram.io or any other web tool. There is no browser automation available in this environment. The user (or whoever runs this skill) pastes `erd.dbml` into their own dbdiagram.io project and uses that site's own Export feature to get a PDF/PNG. Say this explicitly if asked — never imply that step is automated.

## Output bundle

```
docs/delivery/SolutionArchitecture/
├── diagram-1-application-landscape.drawio
├── diagram-1-application-landscape.drawio.svg
├── diagram-2-application-interaction.drawio
├── diagram-2-application-interaction.drawio.svg
├── diagram-3-data-layer.drawio
├── diagram-3-data-layer.drawio.svg
└── erd.dbml
```

The export pipeline lives in this skill at `templates/export.sh` (drawio → svg only) and is called directly from there with the output folder as its argument — **do not copy it into the project**. The ERD has no export pipeline of its own (see Phase 8) — it's validated, not "exported."

---

## Phase 1 — Pre-flight checks

### 1.1 Confirm this is a backend project
Same as `generate-hld`: look for `*.csproj`/`*.sln` (or `pom.xml`/`go.mod`/`requirements.txt` for other stacks). If nothing matches, stop and ask the user to confirm the directory.

### 1.2 Detect operating system
Run `uname -s` once. `Darwin` = macOS, `Linux` = Linux.

### 1.3 Verify required tools

| Tool | What it does | Detection | Install (macOS) | Install (Linux) |
|---|---|---|---|---|
| `drawio-desktop` | Exports `.drawio` → `.svg` from CLI | `ls /Applications/draw.io.app/Contents/MacOS/draw.io` (macOS) or `command -v drawio` | `brew install --cask drawio` | see [drawio-desktop releases](https://github.com/jgraph/drawio-desktop/releases) |
| `rsvg-convert` (optional) | Quick local PNG preview only — not part of the deliverable | `command -v rsvg-convert` | `brew install librsvg` | `sudo apt-get install -y librsvg2-bin` |
| `npx` (Node.js) | Validates the generated `erd.dbml` via `@dbml/cli` (Phase 8.4) | `command -v npx` | `brew install node` | `sudo apt-get install -y nodejs npm` |

No pandoc, no python-docx, no python3 — this skill never builds a Word document. `dotnet`/`dotnet-ef` are used for the ERD's primary (command-based) generation path in Phase 8.2 — verify they're available, but note that if the command route fails on config grounds, the fallback path doesn't need them at all.

---

## Phase 2 — Input discovery

Three inputs are required for the diagrams. **Never invent any of them** — if one is missing, stop and ask. (The ERD's source is discovered automatically in Phase 8 — no separate question needed for it.)

### 2.1 Frontend project path
Use `AskUserQuestion`: "Where is the frontend project for this backend?" Options: "I have the path" (verify `package.json` exists) / "I'll paste the package.json" / "No frontend". Only used to correctly name the Presentation-tier box in Diagram 1 (React SPA vs Next.js vs none).

### 2.2 Roles/permissions spreadsheet
Ask: "Where is the business roles/permissions spreadsheet (or list) for the Data Layer diagram?" This must be a source separate from the code — a project's `EnumRole`/`Permission` enum is frequently a simplified subset of the real business roles (integration platforms like Seha often expose many permission IDs; projects commonly map only a business-meaningful subset — collapsing redundant ones — rather than 1:1). Treat the spreadsheet/list as authoritative for **Business Actors**; treat code enums as authoritative only for **how access is implemented**, not for the diagram's actor list. If neither a path nor a pasted list is available, stop and ask — do not invent role names. If the user has genuinely none available, fall back to the code's `EnumRole`/`Permission` enum and say explicitly in the plan (Phase 4) and the verification summary (Phase 10) that Business Actors are code-derived, not from a business-authored source — that's a real accuracy caveat, not a formality.

### 2.3 Confirm component/integration source of truth
Check whether `docs/delivery/HLD/HLD.md` exists in the backend project (produced by the `generate-hld` skill, if it has been run before). If it exists, treat it as source of truth for controllers, application services, external integrations, and auth model — do not re-derive these from scratch. If it doesn't exist, fall back to a direct code exploration (see Phase 5) — do not require the user to run `generate-hld` first.

---

## Phase 3 — Mode detection (CREATE vs UPDATE)

Check if `<backend-project>/docs/delivery/SolutionArchitecture/diagram-1-application-landscape.drawio` and `erd.dbml` (and the other two diagrams) exist.

- **Don't exist → CREATE mode.** Generate everything from scratch.
- **Exist → UPDATE mode.** Read each existing `.drawio` file and summarize its current element set to the user (e.g. "Diagram 1 currently shows: SPA, Backend API, SQL Server, Seha, S3"); for `erd.dbml`, summarize table/FK counts. Ask whether to regenerate everything or only the pieces that look stale against current code/roles/schema. Unlike `generate-hld`'s markdown section-diffing, there is no partial patch here — a regenerated diagram or ERD replaces its whole file, since these are visual layouts and a full schema dump, not prose sections.

---

## Phase 4 — Plan mode (mandatory)

**Always enter plan mode before generating anything.** Use `EnterPlanMode`.

The plan must state:
- Mode: CREATE or UPDATE
- Confirmed inputs: frontend path (or "no frontend"), roles spreadsheet path (or "code-derived, no business source available" — see 2.2), whether `HLD.md` was found and used
- The tiering/grouping scheme proposed for Diagram 1 (this is a judgment call — state it explicitly so the user can correct it before generation)
- A one-line content summary for each of the 3 diagrams
- Which ERD source method will be used (`dotnet ef dbcontext script` succeeded / fell back to model snapshot / fell back to direct entity-class read — see Phase 8.2), and if it's the riskier direct-read fallback, say so plainly

Wait for `ExitPlanMode` approval before writing any files.

---

## Phase 5 — Source exploration checklist

Trimmed to only what feeds these deliverables — do not enumerate package versions or unrelated sections.

**From `HLD.md` (preferred) or direct code exploration (fallback):**
1. Controllers list and what each does
2. Application services, especially integration-facing ones (identity/auth provider client, cloud storage client, mail client, monitoring/APM)
3. External integrations table (name, protocol, purpose)
4. Auth/permission model (how roles/permissions gate access)
5. Data store (engine, ORM)

**From frontend (only if a path/package.json was provided):**
1. Framework + version (React/Next/Vite) — just enough to label the Presentation-tier box correctly
2. Do not re-derive full page/route lists or dependency tables — out of scope for these deliverables

**From the roles spreadsheet (or code fallback, per 2.2):**
1. The full list of distinct business role names (Business Actors)
2. Which actions/services/report-categories each role's permissions grant it (for Diagram 3's actor→service edges)

**For the ERD:** locate the schema source per the priority order in Phase 8.2 — don't read entity classes in detail yet if a model snapshot file exists; that file alone is sufficient.

---

## Phase 6 — Diagram content mapping

This phase has no equivalent in `generate-hld` — it documents the ArchiMate-specific judgment calls so repeated runs stay consistent.

### 6.1 Application Landscape (Diagram 1)
Group components into tiers using plain dashed-rectangle containers (see style rules in Phase 7). A sensible default tiering:

| Tier | Contents |
|---|---|
| Presentation | The frontend SPA/app |
| Core Business | The backend API itself (one Application Component box by default; only decompose into per-controller/module boxes if the user asks for finer granularity) |
| Data | The primary data store, represented as an Application Component (see Phase 7 — Technology-layer shapes are out of scope for this diagram type) |
| Integration | Every external system the backend integrates with (identity provider, cloud storage, mail server, APM, etc.) — shown as peer boxes at the same visual level as Core Business, **not nested inside it** |

Always include external integrations as landscape entries — this diagram's purpose is to show what this solution touches, not just its own internals.

### 6.2 Application Interaction (Diagram 2)
For each external integration, draw one **function → collaboration → interface → external system** chain:
- An Application Function box in the backend, named after the integration-facing service class that owns it
- An Application Collaboration box representing the joint behavior between the backend and the external system
- An Application Interface box representing the exposed access point (the protocol/API)
- The external system itself as an Application Component

Connect them left-to-right with plain labeled edges (see Phase 7 — edge styles). If an integration is a direct instrumentation/library call with no negotiated interface (e.g. an APM agent), it's fine to omit the Collaboration/Interface and connect Function directly to an Application Service box (or directly to the external system's Application Component) representing the external capability.

### 6.3 Data Layer (Diagram 3)
Two stacked dashed-rectangle bands (plain containers, not the native grouping shape):
- **Business Layer band** (top): one Business Actor box per real business role, from the roles spreadsheet — every role, no omissions, no invented roles.
- **Application Layer band** (bottom): Application Services/Components representing the capabilities those roles use (e.g. report management, approval workflow, dashboard/reporting, file storage).
- Association edges cross the band boundary from each actor to the service(s) its permissions grant it, per the roles spreadsheet's action mapping. Avoid drawing an edge from every actor to every service — only draw the ones the spreadsheet actually supports.

**Layout warning (learned the hard way):** with more than a handful of actors/services, a naive grid + straight drop-lines WILL cross through unrelated boxes and their labels — actors sharing a row block any direct sideways exit, and actors sharing a column block any direct vertical drop. Use the gutter-routing approach from Phase 7's worked example: route each edge sideways into the clear gap *between* columns (never through a row), straight down that gap to below the entire service row, then sideways in that clear space, then up into the target's bottom edge. Verify visually (render to PNG, see Phase 10.9) before calling any diagram with more than ~6 actors done — don't assume geometry is correct just because the XML is well-formed.

---

## Phase 7 — Diagram XML authoring

### 7.1 Read the templates first
Read all three example files in this skill's `templates/` folder before writing new ones:
- `templates/example-diagram-1-application-landscape.drawio`
- `templates/example-diagram-2-application-interaction.drawio`
- `templates/example-diagram-3-data-layer.drawio`

These are working, drawio-desktop-verified XML. Adapt them — same structure and style strings, with labels/boxes matching the actual project.

### 7.2 Validated ArchiMate 3 style strings — use these verbatim

These were confirmed correct by rendering a real test file through the actual `drawio-desktop` CLI and visually inspecting the output: they render as a plain colored rectangle with the correct small ArchiMate type-icon badge in the top-right corner, matching the client's template convention.

| Element | Style string |
|---|---|
| Business Actor | `shape=mxgraph.archimate3.application;appType=actor;archiType=square;fillColor=#FFFF99;strokeColor=#000000;html=1;whiteSpace=wrap;fontSize=11;align=center;verticalAlign=middle;` |
| Application Component | `shape=mxgraph.archimate3.application;appType=comp;archiType=square;fillColor=#99CCFF;strokeColor=#000000;html=1;whiteSpace=wrap;fontSize=11;align=center;verticalAlign=middle;` |
| Application Function | `shape=mxgraph.archimate3.application;appType=func;archiType=rounded;fillColor=#99CCFF;strokeColor=#000000;html=1;whiteSpace=wrap;fontSize=11;align=center;verticalAlign=middle;` |
| Application Interface | `shape=mxgraph.archimate3.application;appType=interface;archiType=square;fillColor=#99CCFF;strokeColor=#000000;html=1;whiteSpace=wrap;fontSize=11;align=center;verticalAlign=middle;` |
| Application Collaboration | `shape=mxgraph.archimate3.application;appType=collab;archiType=square;fillColor=#99CCFF;strokeColor=#000000;html=1;whiteSpace=wrap;fontSize=11;align=center;verticalAlign=middle;` |
| Application Service | `shape=mxgraph.archimate3.application;appType=serv;archiType=rounded;fillColor=#99CCFF;strokeColor=#000000;html=1;whiteSpace=wrap;fontSize=11;align=center;verticalAlign=middle;` |

Standard layer colors: Business = `#FFFF99` (yellow), Application = `#99CCFF` (blue/cyan).

For containers/zones/logical-layer bands, use a plain rectangle rather than the native `shape=mxgraph.archimate3.application;appType=grouping;...` shape — the client's own reference diagrams render these as plain dashed boxes with no corner icon, so this is simpler and matches the template look directly:

```
rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#666666;dashed=1;verticalAlign=top;fontStyle=1;
```

**Note on a red herring:** every `.drawio.svg` file drawio exports contains a `<switch>` fallback block ending in the literal text "Text is not SVG - cannot display" (a link to drawio's own FAQ page) — this is a **standard, harmless compatibility fallback present in every drawio SVG export** for legacy renderers that don't support `foreignObject`-based text, confirmed present even in this repo's already-shipped `generate-hld` diagrams. It is invisible in any modern SVG viewer (browsers, Word, GitHub). Do not treat its presence as an error signal.

**Scope note:** the client's own reference diagrams for these 3 types use only Application-layer (blue) and Business-layer (yellow) elements — no Technology-layer/Node boxes (those belong to a separate Infra Zoning diagram, out of scope here). Represent any data store as an Application Component, not an untested Technology-layer shape. If a future need arises for Technology-layer elements, hand-render-test the shape through the drawio-desktop CLI first (same process used to validate the table above) before adding it to this table.

### 7.3 Edges
Use plain labeled orthogonal edges, same convention as `generate-hld`'s diagrams:
```
edgeStyle=orthogonalEdgeStyle;html=1;fontSize=11;
```
Do not use ArchiMate-specific relationship arrowheads (dotted realization, filled-triangle serving/access arrows, etc.) — these have not been render-tested. If precise ArchiMate relationship notation is needed later, validate the exact style string by rendering a small test file through the drawio-desktop CLI first, the same way the shapes above were validated, before adopting it here.

For any many-to-one or one-to-many fan pattern (Diagram 3 especially), route with explicit `exitX`/`exitY`/`entryX`/`entryY` plus an explicit `points` array — do not rely on drawio's default automatic routing once more than 2–3 edges share a source or target, it will route through other shapes. See Phase 6.3's layout warning.

### 7.4 Save
Save as `diagram-1-application-landscape.drawio`, `diagram-2-application-interaction.drawio`, `diagram-3-data-layer.drawio` in the output folder.

---

## Phase 8 — ERD / DBML generation

This phase has no equivalent in `generate-hld` either. Goal: one `erd.dbml` file, accurate to the real persisted schema, ready to paste into dbdiagram.io.

### 8.1 Is an ERD in scope?
Confirm the backend actually has a relational schema (EF Core is the common case in this org's .NET backends). If there's no persistent relational store, skip this phase and say so plainly in Phase 10's summary ("N/A — no relational schema") — don't force an ERD that doesn't apply.

### 8.2 Find the ground-truth schema source — command first, manual only as a fallback

**Always attempt the command first.** Don't reach for the manual method just because it's available — a real tool run against the live model catches drift that a checked-in snapshot file might miss (e.g. an uncommitted entity change).

1. **Try `dotnet ef dbcontext script --project . --startup-project . -o <tmp-file>` (or the equivalent for the project's ORM) first, always.**
   - If it fails because the project doesn't build for an unrelated reason (e.g. a stale/corrupt `obj/project.assets.json`), fix that specific build error (`dotnet restore --force` fixes this exact symptom) and retry the command once.
   - **If it fails with a config-validation error** — missing `appsettings.json`, a required config section, or "DbContextOptions could not be resolved" while booting the full app host — **that specific failure is the trigger to fall back to step 2.** Don't chase down every missing config value one at a time just to force the command to succeed; don't stub config or add a design-time factory as a first resort either — go straight to the fallback.
   - If it succeeds, use its SQL output directly as the schema source for Phase 8.3 and skip step 2 entirely.

2. **Fallback — generate the DBML yourself, then validate it by command.** Only reached when step 1's command fails specifically due to app configuration, as above.
   - Prefer reading the EF Core model snapshot file if one exists: `**/Migrations/*ModelSnapshot.cs` (e.g. `Infra/Data/Migrations/DataContextModelSnapshot.cs`). EF Core auto-maintains this file to represent the complete current schema — every table, column, type, nullability, max length, primary key, foreign key, cascade behavior, and index — so reading it directly is reliable and requires nothing to build or run.
   - If no snapshot file exists either, read the entity classes directly (`Domain/Entities/*.cs` or equivalent) plus any Fluent API configuration (`OnModelCreating`, entity `IEntityTypeConfiguration` classes). This is the riskiest path: EF Core conventions (shadow FK column names, join-table naming for many-to-many, default max lengths, identity vs. externally-assigned keys) can silently diverge from what's inferable from the C# alone. Flag every assumption you're not fully certain of, in the plan and in the ERD's own `Project` note (8.3).
   - Whichever of these two you use, **the mandatory `dbml2sql` validation in Phase 8.4 is what stands in for the command-level generation you didn't get** — don't skip it or treat it as optional just because this path already involved careful reading.
   - Mention, as an optional aside (not a blocker), that adding a small `IDesignTimeDbContextFactory<TContext>` would let the command-based route succeed on future runs — but don't add it yourself or wait on that decision before proceeding with the fallback now.

### 8.3 Translate the schema into DBML

Read `templates/example-erd.dbml` first — it demonstrates every convention below in a small, working example. Then write a single `erd.dbml`:

- **Column types**: use the exact underlying SQL type from the source (e.g. `nvarchar(300)`, not a generic `varchar`) — precision matters, don't substitute a "close enough" type.
- **Keys**: `[pk, increment]` for identity/auto-increment columns; `[pk]` only (no `increment`) for externally-assigned IDs — and call this out with a `note:`, since it's an easy detail to miss and it's meaningful (e.g. a `Users` table whose `Id` is synced from an external identity provider, not generated by this database).
- **Nullability**: mark required columns `[not null]`; leave nullable columns unmarked (DBML's default is nullable).
- **Foreign keys / `Ref:` lines**: draw a `Ref:` line **only** for relationships the ORM actually configured with a real foreign-key constraint (in EF Core terms: `HasForeignKey` + a navigation property in the model). For columns that merely *look* like a reference but aren't formally configured (common with externally-sourced IDs — e.g. a `CreatedBy` int that logically points at a `Users` table but has no navigation property in the model) — **do not draw a `Ref:` line**; add a short column-level `note:` instead. This is the difference between documenting the database as it truly is vs. as it's loosely intended by the code's author — don't blur that line, and don't let a plausible-looking column name substitute for checking the actual model.
- **Composite keys**: use the `indexes { (ColA, ColB) [pk] }` block syntax for join tables.
- **Defaults**: carry over `[default: ...]` where the source declares one.
- **Table groups**: optionally group tables (`TableGroup`) by domain area for readability — visual only, no schema meaning, skip if the schema is small.
- **Project note**: add a `Project` block at the top with a `Note:` stating exactly what the DBML was generated from — the snapshot file path, or "`dotnet ef dbcontext script` output", or "direct entity-class read — some EF Core conventions inferred, verify before relying on this" — so a future reader knows how much to trust it.

### 8.4 Validate the DBML

Round-trip it through a real parser before considering it done — do not skip this, a syntactically broken DBML file is worse than no file, since it looks done at a glance:

```bash
npx --yes -p @dbml/cli dbml2sql erd.dbml --mssql -o /tmp/erd_check.sql
```

(swap `--mssql` for `--postgres` / `--mysql` to match the actual database engine). If this fails, the DBML has a syntax error — fix it. If it succeeds, sanity-check the output: the `CREATE TABLE` count and `FOREIGN KEY` count in the generated SQL should match what you read from the source in 8.2 exactly.

### 8.5 Save
Save as `erd.dbml` in the output folder, alongside the 3 diagrams.

### 8.6 What this skill does not do
It does not upload, paste, click, or export anything on dbdiagram.io or any other website — there is no browser automation available in this environment. If asked whether the PDF/PNG export itself can be automated, say clearly: no, that step is manual — paste `erd.dbml` into the target dbdiagram.io project and use that site's own Export feature.

---

## Phase 9 — Export diagrams to SVG

Call `templates/export.sh` from the skill folder (never copy it into the project):

```bash
bash <skill-folder>/templates/export.sh <backend-project>/docs/delivery/SolutionArchitecture
```

For example, when this skill lives at `<project>/.claude/skills/generate-solution-architecture/`:
```bash
bash .claude/skills/generate-solution-architecture/templates/export.sh docs/delivery/SolutionArchitecture
```

Pass `--png` as a second argument to also render quick local preview PNGs (not part of the deliverable, useful only for your own verification pass in Phase 10). This step only applies to the 3 `.drawio` diagrams — `erd.dbml` has no export step (see Phase 8.4 for its own validation).

---

## Phase 10 — Verification pass (mandatory)

After generation, verify everything. Print a ✓/✗ summary table to the user, covering all 4 deliverables (mark the ERD row "N/A" if Phase 8.1 determined it's out of scope).

**Diagrams:**
1. **No off-catalog shape** — grep all 3 `.drawio` files for `appType=grouping`; must be zero matches (containers should use the plain-rectangle style from 7.2, not this shape — a style choice, not a bug fix; see the note there).
2. **Style-string fidelity** — every `shape=mxgraph.archimate3.application;...` cell uses one of the 6 validated `appType`/`archiType` combinations from Phase 7.2 verbatim.
3. **Layer color correctness** — every Business Actor is `#FFFF99`; every Application-layer element is `#99CCFF`; no off-palette colors.
4. **Business Actor completeness** — Diagram 3 contains exactly as many Business Actor boxes as the roles spreadsheet (or code fallback) has distinct roles, labels matching exactly (no invented, no dropped roles).
5. **Integration completeness** — Diagram 1's integration tier and Diagram 2's external-system boxes name the same set of external systems, matching the spelling used in the External Integrations source (`HLD.md` or direct exploration) — no more, no fewer, no naming drift.
6. **Function-to-code traceability** — every Application Function label in Diagram 2 corresponds to a real service class named in the source material.
7. **Containment hygiene** — every child shape's geometry sits fully inside its parent dashed-container's `x/y/width/height` bounds.
8. **Export succeeded** — all 3 `.drawio.svg` files exist and are non-zero size.
9. **Visual spot-check** — convert to PNG (via `export.sh --png` or `rsvg-convert` directly) and confirm each shape shows its expected corner icon badge rather than a blank rectangle, AND confirm (for Diagram 3 especially) that no edge or label visually crosses through an unrelated box — a blank box indicates a dropped/mistyped `shape=` string; a crossing line indicates the routing warning in Phase 6.3 was skipped.

**ERD:**
10. **DBML parses** — `erd.dbml` round-trips through `dbml2sql` (Phase 8.4) without error.
11. **ERD completeness** — the `CREATE TABLE` and `FOREIGN KEY` counts from the `dbml2sql` output match the source schema (model snapshot / `dbcontext script` output) exactly. If the direct-entity-read fallback (8.2 option 3) was used, say so here explicitly as a lower-confidence result.

---

## Tone & quality bar

- **Honesty over completeness.** If a role, integration, component, or schema detail can't be confirmed from the source material, say so — don't invent it.
- **Never reconstruct ArchiMate style strings from memory or by guessing similar-sounding names.** Use only the table in Phase 7.2. If a new shape type is genuinely needed, render-test it by hand through the drawio-desktop CLI first — the same way every shape in this skill was validated — before adding it to the table and using it in generated output.
- **Never draw a `Ref:` line on a guess.** Only relationships the ORM formally configured become `Ref:` lines in the ERD — everything else is a `note:`, however obvious the column name looks.
- **No padding.** Don't add tiers, roles, integrations, or schema relationships that aren't supported by the source material.

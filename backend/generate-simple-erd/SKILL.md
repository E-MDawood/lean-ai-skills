---
name: generate-simple-erd
description: Generate a simple ERD document that lists the database tables without columns, each with a one-line description, plus any stored procedures and optional links between tables. It's built from whichever is more advanced: the sprint planning docs (produced by the sprint-planning skill) or the actual code. If the planning is ahead of the code it uses the planning; if they match it uses the code. Outputs SimpleERD.docx with a table-overview diagram to /docs/delivery/SimpleERD/. Use when the user asks for a "simple ERD", "tables list", "high-level ERD", "ERD without columns", "list of tables and stored procedures", or similar. For a full column-level ERD (.dbml), use `generate-solution-architecture`.
---

# Generate Simple ERD

A high-level data model document:

- **Tables, without columns.** Each gets a one-line description of what it holds.
- **Links between tables are optional.** Include them only where the source states them.
- **Stored procedures, if any.** Each gets a one-line purpose.

The column-level ERD (`erd.dbml`) is `generate-solution-architecture`'s job, so don't list columns, types or keys here.

## Output bundle

Everything lands in `<backend-project>/docs/delivery/SimpleERD/`:

- `SimpleERD.docx`: the deliverable
- `SimpleERD.md`: markdown source
- `diagram-1-tables.drawio` + `.drawio.svg`: table boxes (names only), with links if included

Build with the shared pipeline `../generate-hld/templates/regenerate.sh <folder> SimpleERD`. **Don't copy it into the project.**

---

## Phase 1: Pre-flight

Follow `../generate-hld/SKILL.md` § "Phase 1: Pre-flight checks". That covers the backend project check, the OS, and the tools `pandoc`, `rsvg-convert`, drawio-desktop, `python3` and `python-docx`. Ask before installing anything.

## Phase 2: Pick the source: planning or code

Follow `../generate-hld/references/planning-vs-code.md` §1-§3 and apply **Policy C (most advanced wins)**. Here, "design-relevant" means **data items only**: tables (new, changed, renamed, removed) and stored procedures.

- **Planning is ahead** (at least one planned table or stored procedure that isn't in the code): use the planning for the latest sprint with planned-only data items. The document is then code as built + planned items from sprints ≤ N (reference §5).
- **Planning matches the code, or there's no planning**: use the code.
- Announce the choice in one line with the counts. It also goes in the plan (Phase 4), where the user can correct it, so don't ask a separate question.

## Phase 3: Collect tables and stored procedures

### From the code (always, as the baseline)

**Tables.** Use the actual persisted schema. Check these in order and stop at the first that's authoritative for the project:
1. EF Core model snapshot (`Migrations/*ModelSnapshot.cs`): `b.ToTable("X", "schema")` entries
2. `DbContext` `DbSet<>` properties + `IEntityTypeConfiguration<>` classes (`ToTable(...)`)
3. `.sql` scripts / database projects (`*.sqlproj`, `CREATE TABLE`)

Also include tables owned by libraries if they live in the same database (e.g. the Hangfire schema). List them as one grouped row ("Hangfire job storage: 11 tables, `HangFire` schema") rather than one row each.

**Stored procedures:**
- `CREATE PROCEDURE` / `CREATE OR ALTER PROCEDURE` in `.sql` files and inside migrations (`migrationBuilder.Sql(...)`)
- Call sites: Dapper `commandType: CommandType.StoredProcedure`, `EXEC`/`FromSqlRaw`/`ExecuteSqlRaw` strings, `usp_` names

A procedure called from code but not defined in the repo still gets a row; mention in the chat that it's defined elsewhere.

**Document databases (MongoDB, Cosmos DB …).** Treat each database as a schema group and each collection as a table, and say "collection" in the document. Take collection names from the code's collection-name constants and `GetCollection` calls, plus the collections every module gets from shared registrations (counters, outbox, relay state …). There are no stored procedures, so section 3 is one line: "No stored procedures." Relationships come only from explicit references: keyed by another collection's id, rebuilt from another collection, or stated in the project's data docs.

**Descriptions.** Write one line per table or procedure, based on the entity's XML doc comment, the plan, or how the code uses it, in that order of preference. If you can't tell what it holds, write "Purpose not documented" rather than guessing from the name.

**Links (optional).** Take them only from navigation properties / `HasOne`/`HasMany`/`HasForeignKey`, FK constraints in SQL, or explicit relationships in the plan. Never infer a link from column names alone.

### From the planning (only when the source is planning for sprint N)

From the sprint ≤ N plan files, take every table and stored procedure the plan names: new ones, changes, renames and removals. Apply reference §5. Removed tables disappear. Renamed tables appear under the new name, with "(was `Old`)" in the description. A plan that describes data without naming a table ("store the referral attachments") becomes an open point, not an invented table.

## Phase 4: Plan (in the chat, before writing)

Before writing anything, show the user the plan. **Don't enter plan mode** (`EnterPlanMode`): stay in the current mode. Write the plan in the chat as a short message, then go straight on to generating. Don't stop to wait for approval. If the user replies with a correction, apply it and regenerate.

The plan states:
- **Basis**, with the counts: "<n> tables (<p> planned), <m> stored procedures (<q> planned)"
- **Links:** include or omit. Default to include if the source states relationships. The user can turn them off.
- **Mode:** CREATE, or UPDATE if `SimpleERD.md` exists. UPDATE replaces rows that changed, keeps manual description edits on unchanged rows, and warns if the hidden basis comment on the first line differs.
- **Open points** (chat only, never in the document)

Then continue to Phase 5.

## Phase 5: Write `SimpleERD.md`

The document is for other teams (business, architecture, DBAs), who care about the tables and nothing about the build. **Follow `../generate-hld/references/planning-vs-code.md` §6 (What the reader sees).** In short, the document has:
- no basis line, sprint numbers or "generated from the planning / the code"
- no status labels
- no open points
- no references to code files, classes or planning/docs files
- no source column for relationships

Every table is simply part of the data model, whether built or planned.

```markdown
<!-- basis: <hidden basis comment from reference §5> -->
# <System name>: Simple ERD

One or two sentences: what the database holds and how it is organised.

## 1. Tables
One table per database schema (`### Schema: dbo`, `### Schema: api` …), rows sorted by name:

| Table | Description |
|---|---|
| `Claims` | Submitted claims, one row per claim submission |
| `ClaimAttachments` | Files attached to a claim |

![Figure 1: Tables overview](diagram-1-tables.drawio.svg)

## 2. Relationships        ← only if links are included
| From | To | Relationship |
|---|---|---|
| `ClaimAttachments` | `Claims` | Many attachments belong to one claim |

## 3. Stored Procedures     ← if none: "No stored procedures." (one line)
| Procedure | Purpose |
|---|---|
| `api.usp_GetClaimById` | Returns one claim with its latest status |
```

Rules:
- No columns, data types, keys or indexes anywhere in the document.
- Use table names exactly as they appear in code or the plan, schema-qualified where the project uses more than one schema. Descriptions are plain language: no class names, use-case or rule IDs, ticket keys, or "pending the BA".
- A planned data area the plan doesn't name a table for stays out of the document; report it in the chat as an open point.

## Phase 6: The tables diagram

Write `diagram-1-tables.drawio`: one box per table containing **only its name**. Group the boxes in a container per schema. Draw every table box the same way, built or planned: no dashed borders, no status legend. If links are included, draw one plain edge per relationship, labelled `1-*` / `1-1` / `*-*` (plain hyphens). Collapse library tables (e.g. Hangfire) into a single box.

Reuse the `mxGraphModel` structure and the red/pink data palette from `../generate-hld/templates/example-diagram-3-dependency-mapping.drawio`. Lay boxes out on a grid with about 20 px gaps. For more than about 30 tables, skip the edges; the caption says the relationships are listed in section 2.

**Plain-text labels only.** Use `html=0` and no `whiteSpace=wrap` in every cell style, and break lines with `&#xa;` in the label. With HTML or wrapped labels, drawio exports the text as `foreignObject`: Word and `rsvg-convert` can't render that, and the image gets a "Text is not SVG - cannot display" footer. Route edges so they never cross a box: connect from container edges with `exitX`/`exitY`/`entryX`/`entryY` rather than between inner boxes.

## Phase 7: Build

```bash
bash ../generate-hld/templates/regenerate.sh <backend-project>/docs/delivery/SimpleERD SimpleERD
```

If a step fails, report the step and its output.

## Phase 8: Verify and report

Print a ✓/✗ table:
- Every table and procedure from the code exists in the code source from Phase 3, and none is missing (compare counts with the snapshot / `CREATE` statements).
- Every table from the plan traces to a sprint ≤ N plan file. Cite it in the chat, not in the document.
- Every relationship traces to a navigation property, FK or plan line. Cite the source in the chat.
- **Reader check:** the `.md` (outside the first-line comment) has none of the items in reference §6. Search it for `Planned`, `Existing`, `sprint`, `Open`, ticket and use-case IDs, `.cs`, `docs/`, `src/`, plus the em dash (U+2014) and en dash (U+2013) in the `.md` and the `.drawio`, and fix any hit.
- The diagram box count equals the table rows (counting collapsed library groups as one).

End the chat report with the basis, the open points, and any gaps between the code and the project's own data docs.

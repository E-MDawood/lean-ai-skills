# Planning vs. code: choosing the source of a design document

Shared by `generate-hld`, `generate-simple-hld` and `generate-simple-erd`. Each skill says which **decision policy** (§4) it uses; the discovery and comparison steps (§1-§3) are the same for all three.

The question this file answers: **is the planning ahead of the code, and if so, which sprint should the document describe?**

---

## 1. Find the planning docs

Planning docs are produced by the **`sprint-planning` skill**. It owns their layout, so don't hard-code it here. Before looking for planning, read `sprint-planning/SKILL.md` in the sibling skill folder (`.claude/skills/sprint-planning/`), plus the `references/` files it points to for the outputs you need, and use what it says *at run time* for:

- where a sprint's files live, and how sprints are numbered
- how batched sprints are laid out, and which files are the per-batch ones versus the sprint-root overview
- what each phase's output file is called, and how it's structured

When choosing which of those outputs to trust, use this order of authority. It's defined by what each phase produces, not by file name:

1. **The detailed development plan** (sprint-planning's dev-plan phase). This is the primary source, because sprint-planning requires it to name exact entities, fields and endpoints.
2. **The API contract files** (its contract phase), for planned API surface.
3. **The scope/analysis notes** (its scope-judgment phase), for which areas a story touches.
4. **The task breakdown** (its task phase), only to see what's planned versus done. See §3.
5. **The raw story capture and the BRD.** Use these only to fill gaps the plan leaves. Never let them override the plan.

Never use the **codebase exploration** output as planning. It's a snapshot of the code at planning time, not planned scope.

If the `sprint-planning` skill isn't installed, or the project's planning docs don't follow its layout (e.g. loose design docs under `docs/plans/` or `docs/stories/`), read whatever planning docs exist there, treating each as one unit. Ask the user which sprint one belongs to only when the policy in §4 needs a sprint.

If there are no planning docs at all, ask the user with `AskUserQuestion`: "I couldn't find planning docs. Where are they?" Options: "I'll give a path" / "I'll paste them" / "No planning docs, use the code". Never invent planned scope.

## 2. Extract the planned design

From the planning sources, list the design-relevant items the calling skill needs. Skip anything purely UI-cosmetic or test-only:

| Kind | Examples |
|---|---|
| Components | new services/modules, new frontend app, background jobs, messaging |
| Integrations | external systems, HTTP clients, queues, files/SFTP, identity providers |
| API surface | new/changed controllers or endpoint groups |
| Data | new/changed tables, removed tables, stored procedures, views, TVPs |
| Cross-cutting | auth changes, new config/environments, monitoring |

For each item, record the sprint and the file it came from, so the document and the user prompt can cite it.

## 3. Compare against the code

For each planned item, check whether it exists in the code (same discovery the calling skill does: controllers/routes, `DbSet<>`/migrations/`.sql` files for tables, `CREATE PROCEDURE` / `usp_` names in `.sql` files and Dapper/EF calls for stored procedures, `HttpClient` registrations for integrations, etc.). Classify:

| Status | Meaning |
|---|---|
| **Built** | Present in code as planned. |
| **Planned only** | In the plan, not in code yet. |
| **Diverged** | Built, but differently from the plan (renamed, split, dropped). Code wins for what exists; mention the divergence to the user. |

The task breakdown's done markers (whatever format sprint-planning currently uses) are a hint, not proof. A task marked done with no matching code is **Planned only**. A task not marked done whose code exists is **Built**.

Result: **planning is ahead** if at least one sprint has a design-relevant **Planned only** item. Otherwise **planning matches the code** (or there is no planning).

No code yet (fresh repo, nothing under the backend project but scaffolding) → every planned item is **Planned only**.

## 4. Decision policies

### Policy A: Ask (used by `generate-hld`)

- **Planning matches the code** → use the code. Say so in one line ("Planning for sprints 1-4 is fully built; generating from code.") and continue.
- **Planning is ahead** → **warn and ask** before anything else. Use `AskUserQuestion` with two questions in one call:
  1. *"Planning docs are ahead of the code: <n> items planned but not built (e.g. <2-3 concrete examples with sprint>). Generate the HLD from the code as built, or from the planning?"* Options: "Code as built" / "Planning".
  2. *"Which sprint should the HLD describe?"* Options: the sprints that have Planned-only items, latest first (max 4; the latest one marked "(Recommended)"). Only meaningful for "Planning"; ignore the answer if the user picked "Code as built".

### Policy B: Planning-first (used by `generate-simple-hld`)

The document is normally produced at the start of a sprint, before code exists, so planning is the expected source.
- Sprint: reuse it if it's established in the conversation; otherwise default to the **latest** sprint folder and state it in the plan the skill shows in the chat (its "Plan" phase) rather than asking a separate question. Ask with `AskUserQuestion` only when two or more sprints have Planned-only items and none is obviously current.
- Existing code (if any) is the baseline the plan builds on; still read it so the document doesn't contradict what's already there.

### Policy C: Most advanced wins (used by `generate-simple-erd`)

- **Planning is ahead** → use the planning, for the **latest** sprint with Planned-only items. Announce it ("Planning (sprint 6) is ahead of the code: 3 tables and 1 stored procedure planned but not built; generating from planning.").
- **Planning matches the code** → use the code.
- No question needed. The choice goes in the plan the skill shows in the chat, and the user can correct it there.

## 5. What "generate from planning for sprint N" means

The document describes the system **as it will be at the end of sprint N**:

> code as built **+** every Planned-only item from sprints ≤ N **−** anything the plans for sprints ≤ N remove

- Items from sprints **after** N are excluded.
- For **Diverged** items, the code's version wins unless a sprint ≤ N plan explicitly changes it again.
- When a plan is too vague to name something (e.g. "store the referral data" with no table name), describe it at the level the plan supports and list it as an open point to the user, never invent a name.

The basis is for the user and for later updates, **never for the reader**. Record it only as an HTML comment on the first line of the `.md` source. pandoc drops comments, so it never appears in the `.docx`:

```markdown
<!-- basis: planning sprint 6 (<plan file(s)>) on code <short git SHA>, generated 2026-11-09 -->
```

or `<!-- basis: code <short git SHA>, generated 2026-11-09 -->`. Get the SHA with `git rev-parse --short HEAD`; skip it if the repo has no commits. Also tell the user the basis in the chat when the run ends.

## 6. What the reader sees (all three skills)

The documents are read by other teams: business, architecture, DBAs, partners. They want the system, not how far the build has got. So the planning-vs-code work above stays **behind the scenes**. The document describes one complete system, written in the present tense ("The platform submits approved COCs to Etimad"), whether a part is built or only planned.

The `.docx` never contains:

| Not in the document | Where it goes instead |
|---|---|
| Basis line, sprint numbers, "generated from the planning / the code" | HTML comment in the `.md` (§5) and the chat |
| Status columns or labels: Existing, Planned, Partial, Prototype, "to add", "not built yet" | Nowhere. Every item is simply part of the system |
| Dashed or otherwise "planned" styling and legends in diagrams | Nowhere. All boxes are drawn the same way |
| Open points, open questions, pending decisions and their IDs (OD-1, G2, PM1, Q4 …) | The chat, at the end of the run |
| References to repos, code files, classes, config keys, endpoint paths in config, or planning/docs files | Nowhere. Name things by what they are ("the Claims module", "the eligibility engine") |
| Delivery-process IDs: Jira keys, use-case and business-rule IDs, BRD versions, team or person names | Nowhere |

**No long dashes.** Never use the em dash (U+2014) or the en dash (U+2013) anywhere in the document, diagrams included: titles, headings, captions, tables, box labels. Use a colon in titles and headings ("Platform: High-Level Design"), parentheses or a comma in text, and a plain hyphen for ranges ("2-4", "1-*").

What stays: system, component, database and table names, technologies and versions, external systems and protocols, plain-language descriptions.

**When an item exists only in the plan and the plan is too vague to describe it properly**, leave it out of the document and report it in the chat as an open point. Don't put a placeholder in the document.

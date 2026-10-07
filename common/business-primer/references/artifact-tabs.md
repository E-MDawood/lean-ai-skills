# Artifact tabs (Phase 4)

The artifact is one HTML page with a sticky tab bar and deep links by bare `#id` (tab ids and section ids). Load the Artifact quickstart / design guidance first. Utilitarian and polished, light and dark themes, works at phone width. Name it after the domain (for example "Medical Authorizations Guide").

If the quality verdict is Poor, add a warning banner above the tabs (see `quality-assessment.md`).

## How to choose the tabs

The question is always: **what does a developer need to understand this particular business?** A tab earns its place when the material has enough substance on that topic that a newcomer would otherwise have to piece it together from many stories.

1. Start from the **core tabs** below. Every business has them, though their content and names adapt (for example "Statuses" may be "Order lifecycle").
2. Go through the **optional tabs** and check each one's signals against the material. Count the evidence.
3. Merge thin topics into a related tab rather than making a tab with three lines. Split a tab when it gets long and has two clear audiences.
4. Order tabs the way a newcomer learns: what it is → who uses it → what it touches → how things move → the rules → reference material → what's unclear → deep dives.
5. Propose the plan to the user with one line of evidence per tab, and what you left out and why. Adjust, then build.

### Example plans

| Business shape | Likely tabs beyond the core |
|---|---|
| Integration hub (partners call our APIs, we call national services) | System map, Integrations, Notifications |
| Back-office portal (many screens, few integrations) | Screens and navigation, Permissions by screen |
| Pricing, billing or payroll | Calculations (formulas, worked examples), Data model |
| Case or approval workflow | Workflow (steps, approvers, SLAs), Escalations |
| Reporting or analytics | Reports and KPIs (definitions, filters, sources) |
| Regulated domain | Compliance and retention |

## Core tabs (always)

### Overview
- Two short paragraphs: what the business is, what our system does in it. Define the 2-3 core actors in passing.
- Key-fact tiles only if the numbers mean something.
- A simple SVG flow of the main lifecycle (5-7 stages; numbered only if it is a real sequence), with any loops.
- Core concepts card (for example parent vs child record) and an out-of-scope card.

### Users and roles
- One card per organization or role (and the system actor if automated jobs act): channel (screens, API, both), what each can do, what it receives.
- An action × role matrix; mark contradictions with a "?" pill.
- One sentence on data scope (who sees what).
- Rename to fit: "Roles", "Personas", "Who uses it".

### Lifecycle and values
- State diagrams for each main object, transitions labelled by trigger and source ID.
- A searchable, group-filterable catalog of **every** list of values in the material: field, where it appears, every code with meaning, a **"Used on"** line (which object it belongs to), a note, and a "!" pill when inconsistent or incomplete.

### Key rules
- Cards by area. Each rule ends with its source ID. "More ↗" links to deep dives.

### Glossary
- Term, original-language label, short definition, "more ↗" where a deep dive exists.

### Open points
- Topic, what is unclear, working assumption. State the confidence level when material is mixed or poor.

### Extra clarifications
- Built from the user's questions and from tricky areas you find.
- **Topic groups** (A, B, C…), sections numbered (A1, A2…), a table of contents of group cards at the top, "Back to contents" after each section.
- Each section: the direct answer first, then a table or worked example, then source IDs, then any open question it depends on.

## Optional tabs (choose by evidence)

| Tab | Add it when the material shows… | Content |
|---|---|---|
| **System map** | Several external systems, or a multi-part backend the reader must picture | SVG of users, our screens, our backend parts, external systems; labelled inbound and outbound arrows with a legend |
| **Integrations** | Many API or data tables, partner systems calling us, national or third-party services | One row per integration: ID, purpose, direction pill, from → to, sync/async, retries or ACK, use case; filters |
| **Notifications** | Many push or message events, delivery rules, retries | Event → recipient table, payloads, delivery and failure rules, what is *not* notified |
| **Use cases / features** | More than a handful of stories, or the business groups them | Groups as the business defines them, executing vs affected parties, story keys, planned sprint |
| **Screens and navigation** | Many mockups or screen tables | Screen inventory with mockup thumbnails, who sees which screen, actions and buttons per role, navigation flow |
| **Data model** | Many entities and fields, parent/child records, reference data | Entity diagram, key fields per entity, which data is fixed vs editable, reference lists |
| **Calculations** | Prices, taxes, fees, scores, quotas, formulas | Each formula in words and symbols, inputs and sources, rounding, worked examples, who calculates what |
| **Workflow and approvals** | Multi-step approvals, hand-offs, escalations | Swimlane or step list, approver per step, SLAs, what happens on timeout |
| **Deadlines and jobs** | Timers, SLAs, scheduled or automatic changes | Every clock: start, length, unit, what happens when it expires, which job applies it |
| **Reports and KPIs** | Reports, dashboards, metrics | Each report: purpose, filters, columns, definitions, data source |
| **Compliance and retention** | Regulations, audit, data retention, privacy | Rules, retention periods, audit log content, who may see sensitive data |
| **Plan and scope** | A sprint plan that the user asked to see alongside the business | Which features land in which sprint, what is unplanned |

If a topic doesn't fit any of these but clearly dominates the material, create a tab for it.

## Cross-links
- Every Extra clarifications section has a stable id (`x-topic`). Other tabs link to it with small "more ↗" pills: glossary terms, value-list cards, figure captions, rule cards, open-point rows, callouts.
- A click handler switches tab, scrolls to the section and briefly highlights it; loading the page with `#x-topic` does the same.

## Writing
- Write for someone who knows nothing about the business. Active voice, short sentences, real examples from the material.
- Codes and field names exactly as in the source; original-language labels next to translations.
- Say "from general knowledge" for anything not in the documents.

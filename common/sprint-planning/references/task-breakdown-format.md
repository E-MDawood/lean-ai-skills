# Phase 6 reference — Task breakdown → `tasks.md`

## Preconditions

Only generate `tasks.md` once both are true:

1. The dev plan (`stories-plan.md` or the relevant `<feature>-plan.md`) is complete and self-contained.
2. Any API contract inconsistencies (Phase 5) are resolved, and the plan reflects the agreed contract.

`tasks.md` is the bridge between planning and development — it translates the plan into a concrete, ordered, dependency-mapped checklist. Development follows the task list, not the plan directly; the plan is the reference material a task's description points back to when more context is needed.

This repo does not use Task Master AI for this — `.taskmaster/` isn't set up (see `SKILL.md`'s note). Plain markdown checklist.

## Structure

```markdown
# Sprint <number> Tasks

## Tasks

- [ ] **T1** - Add `Report` and `ReportListItem` models _(CSPJ-1501)_ - `src/features/reports/models/report.ts`
- [ ] **T2** - Create `reportsApi` RTK Query slice with `getReports` and `getReportById` _(CSPJ-1501)_ - `src/store/api/reportsApi.ts` - depends on T1
- [ ] **T3** - Build `ReportList` component with pagination _(CSPJ-1501)_ - `src/features/reports/ReportList/` - depends on T2
- [ ] **T4** - Build `ReportDetail` page _(CSPJ-1502)_ - `src/features/reports/ReportDetail/` - depends on T2
- [ ] **T5** - Add routes for `/reports` and `/reports/:id` _(CSPJ-1501, CSPJ-1502)_ - depends on T3, T4
- [ ] **T6** - Write tests for `ReportList` and `ReportDetail` - depends on T3, T4

## Dependency Map

T2 -> T1
T3 -> T2
T4 -> T2
T5 -> T3, T4
T6 -> T3, T4
```

`## Dependency Map` is optional — include it when the dependency graph is non-trivial enough to benefit from a flat summary alongside the inline `depends on` annotations.

## Rules

- **One task per concrete unit of work** — a component, a hook, an API slice, a model file, a test file. Small enough to complete and verify independently.
- **Order by dependency** — a task never appears before something it depends on.
- **Declare dependencies explicitly** with `depends on Tn`.
- **Reference the parent story's Jira key** on every task, so the implementer can trace back to the plan section for full context.
- **Be specific** — target file path, type/component name, or key behavior in the description itself. A task should be actionable without re-reading the full plan.
- **Don't start Phase 7 (implementation) until `tasks.md` exists** — even if the plan feels obvious enough to skip straight to coding.

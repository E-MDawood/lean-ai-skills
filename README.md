# Lean AI Skills

One place for all of Lean's AI agent skills. The skills here support the team's [AI-Driven Workflow](https://muddy-sailor-8f0.notion.site/AI-Driven-Workflow-396d3b57d46180fdab61d9d47ccb444d), which covers planning, development, QA, staging, production and delivery.

Keeping the skills in one repo means every project uses the same, up-to-date version of each skill, instead of copies that drift apart from project to project.

## What is a skill?

A skill is a folder with a `SKILL.md` file inside it. The file starts with YAML frontmatter (`name` and `description`), followed by Markdown instructions for the agent. The agent reads the `description` to decide when to use the skill. You can also call a skill by name with `/<skill-name>`.

Some skills also have supporting folders, such as `scripts/`, `templates/`, `references/`, `assets/` or `data/`.

## Skills

Skills are grouped into three folders by the kind of project they are for:

- [`common/`](common/): skills for both frontend and backend repos
- [`frontend/`](frontend/): skills for React/TypeScript frontend repos
- [`backend/`](backend/): skills for .NET backend repos

### Common

| Skill | What it does |
| --- | --- |
| [estimation](common/estimation/) | Estimates time for Jira stories and produces a sprint estimation Excel file |
| [sprint-planning](common/sprint-planning/) | Plans a sprint end to end, from Jira story capture to tasks and the quality gate |
| [bug-fixer](common/bug-fixer/) | Fixes QA, staging or production bugs from a Jira ticket or a description |
| [code-reviewer](common/code-reviewer/) | Reviews code for bugs, security, performance and style |

### Frontend

| Skill | What it does |
| --- | --- |
| [browser-check](frontend/browser-check/) | Runs the app in a real browser to check a UI change and take screenshots |
| [seha-auth](frontend/seha-auth/) | Gets a dev token for apps embedded in SEHA and writes it to the local env file |
| [forms](frontend/forms/) | Creates and edits forms with react-hook-form and `RenderFormFields` |
| [mock-server](frontend/mock-server/) | Sets up MSW mock API handlers for local development |
| [vitest](frontend/vitest/) | Writes and fixes Vitest tests and the CI test pipeline |
| [fallow](frontend/fallow/) | Analyzes JS/TS code health: unused code, duplication, complexity and more |

### Backend

| Skill | What it does |
| --- | --- |
| [coverlet-tests](backend/coverlet-tests/) | Writes .NET xUnit tests and checks the 70% Coverlet coverage gate |
| [db-standards](backend/db-standards/) | Applies Lean's SQL Server and EF Core database standards |
| [validate-swagger](backend/validate-swagger/) | Validates `swagger.json` against OpenAPI rules and fixes safe issues |
| [generate-deployment-document](backend/generate-deployment-document/) | Generates the deployment document (`.docx`) for staging and production |
| [generate-hld](backend/generate-hld/) | Generates or updates the High-Level Design document |
| [generate-solution-architecture](backend/generate-solution-architecture/) | Generates ArchiMate architecture diagrams and the database ERD |

## Using the skills in a project

Copy the folders of the skills you need into your project's `.claude/skills/` folder. Copy the skill folders themselves, not `common/`, `frontend/` or `backend/`, because the agent only looks one level deep:

```
your-project/
└── .claude/
    └── skills/
        ├── sprint-planning/
        │   └── SKILL.md
        └── bug-fixer/
            └── SKILL.md
```

### With the `lean-skills` CLI

The CLI in [`cli/`](cli/) does the copying for you. It needs Node 18+ and git, and it uses your existing git credentials. Run it from the root of your project:

```sh
# Pull common + frontend skills into ./.claude/skills
npx github:E-MDawood/lean-ai-skills pull --frontend

# Pull common + backend skills (pass both flags for a full-stack repo)
npx github:E-MDawood/lean-ai-skills pull --backend

# Push ./.claude/skills/forms to frontend/forms in this repo, as a pull request
npx github:E-MDawood/lean-ai-skills push --type frontend --name forms
```

- `pull` replaces local skills that have the same name and leaves your other local skills alone.
- `push` replaces a skill with the same name wherever it is in the repo, even in a different folder. It pushes a new `skill/<name>-…` branch and opens a pull request instead of pushing to `main`. If the GitHub CLI (`gh`) isn't installed, it prints the link for opening the pull request yourself.
- `node_modules` and `.DS_Store` are never copied in either direction.

## Adding or updating a skill

1. Create a folder named after the skill (kebab-case) inside `common/`, `frontend/` or `backend/`, or edit an existing one.
2. Add a `SKILL.md` with `name` and `description` frontmatter. Write a clear description, because the agent uses it to decide when to trigger the skill.
3. Put any scripts, templates or reference files next to `SKILL.md` in the same folder.
4. Add the skill to the matching table above and to the AI Skills page in the [AI-Driven Workflow](https://muddy-sailor-8f0.notion.site/AI-Driven-Workflow-396d3b57d46180fdab61d9d47ccb444d) Notion (under AI Resources).

---
name: seha-accounts-check
description: >
  Check a SEHA project's test accounts, roles and permissions in three modes.
  (1) seha: from the PM's standard SEHA accounts workbook (tabs "Services
  Profile", "Permissions", "Roles & Permissions", "Test Users"), log in as
  every test user on a test environment, check each role's service menu and
  that SEHA's token carries exactly the sheet's permission IDs, and generate
  the project's users JSON and permissions reference. (2) app: once the
  project's backend is deployed, check that every SEHA permission code of each
  role maps to the right permission of the app's own token. (3) update: when the
  PM updates the workbook, check only the changed roles and permissions and
  merge the results. Produces a per-role report (correct / issues) with the
  service metadata. Use it when the PM shares or updates the accounts workbook,
  or when asked to "check the SEHA users", "verify the roles and permissions",
  "check the permission mapping", "generate the users.json from the sheet" or
  "the sheet was updated". Builds on the seha-auth skill for logging in.
---

# SEHA accounts check

Every SEHA project gets the same workbook from the PM: the service profile per environment, the SEHA permission IDs, each role with its permissions, and the test users per environment. This skill checks the accounts against it, in three modes:

| Mode | When | Checks | Produces |
|---|---|---|---|
| **seha** | First time, before the app's backend is deployed (or whenever only SEHA's side matters) | Per role: a test user holds it, the service is in its menu, and SEHA's token (`PermissionList`) has exactly the sheet's permission IDs | `docs/seha-auth/users.json`, `docs/seha-auth/permissions.json` (reference), report |
| **app** | Once the backend is deployed and `users.json` exists | Per role in `users.json`: every SEHA permission code in SEHA's token maps (through the reference) to a permission in the app's own token, with nothing missing or extra | Report |
| **update** | The PM changed the workbook (new roles, new permissions, changed IDs or users) | The changed roles only, in seha or app stage | Updated `users.json` and reference (merged), report of the changes |

Nothing here is specific to one project: roles, permissions, service and users come from the workbook, the role entries from what SEHA shows, and the app mapping from the project. Example values below are illustrations.

## Pick the mode first

- **The request is clear** ("check the new sheet", "generate users.json from this workbook", "the backend is deployed, check the mapping", "the PM added roles"): run that mode straight away.
- **It is not clear** (for example only the skill's name, or a workbook path with no ask): look at the project before asking. No `docs/seha-auth/users.json` points to seha mode; `users.json` and `permissions.json` exist and the user shares a workbook points to update mode; a deployed backend with no sheet points to app mode. If it is still ambiguous, ask with AskUserQuestion: "Which check do you need?" with the three modes as options (seha: first check of the sheet and the SEHA accounts; app: check the SEHA to app permission mapping on the deployed backend; update: check only what changed in an updated sheet). For update mode, also ask whether the backend is deployed yet (seha stage or app stage).

## Before you start

- **seha-auth must be installed in the project**: this skill uses its Playwright install (run seha-auth's Step 1 once) and its config, `docs/seha-auth/config.json` (SEHA base URL, service name, the app's iframe host). Python 3 with `openpyxl` is needed for the workbook (`pip install openpyxl` if `import openpyxl` fails).
- **Inputs** (resolve from the project first, ask only for what is missing):
  - the workbook path (seha and update modes; read from disk, never as a chat attachment, see seha-auth Step 3);
  - the environment: DEV, QA or STG. Never PROD: the fixed OTP and test passwords only exist on test environments;
  - the SEHA base URL of that environment (seha-auth config, or the project's env files as seha-auth Step 2 does);
  - the test users' password and OTP: SEHA test accounts normally share `Pass@123` and `1234`; confirm rather than assume;
  - app mode only: the app's iframe host (config `iframeUrlPattern`), where the app keeps its token (localStorage key, default `persist:auth`, field `token`, as seha-auth reads it) and the token claim holding the app's permissions (for example `Permissions`). Find them in the frontend's auth code; ask if unclear.
- **Secrets:** the workbook holds the service's Client Secret. Never print it, write it to a file or commit the workbook; the scripts skip it. Never print raw tokens: the scripts output decoded claims only, without token-like fields.
- Scripts are in `.claude/skills/seha-accounts-check/scripts/`; work files (`sheet.json`, `results.json`, `report.md`) go in the session scratchpad, not the project.

## seha mode

1. **Read the workbook** for the environment:
   `python3 -I scripts/read_sheet.py "<workbook>" DEV <scratch>/sheet.json`
   It prints the service, the counts and any permission label it could not map to an ID (resolve those first).
2. **Write the permissions reference** (every permission with its SEHA ID in every environment, every role with its permissions, the service per environment; no secrets):
   `python3 -I scripts/build_reference.py "<workbook>" docs/seha-auth/permissions.json --keep-app-mapping`
   It is the lasting record of the sheet: the workbook is not kept in the repo, and app and update modes compare against this file. Fill `appPermission` now if the project's permission enum already exists (see "The app mapping" below); otherwise leave it for app mode.
3. **Log in and read SEHA's token per role** (about one minute per role; run it in the background):
   `python3 -I scripts/check.py --sheet <scratch>/sheet.json --out <scratch>/results.json --base-url <SEHA URL> --password '<pw>' --otp 1234`
4. **Report and users JSON:**
   `python3 -I scripts/report.py seha --sheet <scratch>/sheet.json --results <scratch>/results.json --report <scratch>/report.md --users-out docs/seha-auth/users.json --password '<pw>' --existing-users docs/seha-auth/users.json`
   `--existing-users` keeps the `id` of existing entries. `--group auto|yes|no` controls the `category` field (see seha-auth Step 3; decide from the project, `auto` groups when at least one group has two or more roles).
5. **Tell the user** (see "What to report").

## app mode

1. **Check the mapping is filled** in `docs/seha-auth/permissions.json`: every permission the app uses has `appPermission` (see "The app mapping"). Fill or confirm it before running; permissions the app does not use stay `null`.
2. **Log in and read both tokens per role**, from `users.json` (no workbook needed):
   `python3 -I scripts/check.py --users docs/seha-auth/users.json --out <scratch>/results.json --base-url <SEHA URL> --service "<service name>" --app-host <app host> [--app-storage-key persist:auth --app-token-field token]`
   It opens each role, opens the service and reads the app's token from the app iframe once the app has exchanged SEHA's token.
3. **Report:** `python3 -I scripts/report.py app --reference docs/seha-auth/permissions.json --env DEV --results <scratch>/results.json --report <scratch>/report.md --app-claim Permissions`
   Per role: Match, or the app permissions missing from the app token (with the SEHA code that should have produced them), extra app permissions, SEHA codes unknown to the reference, and SEHA permissions with no app mapping.

## update mode

1. **Build the new reference to the scratchpad** (not over the stored one yet):
   `python3 -I scripts/build_reference.py "<new workbook>" <scratch>/permissions-new.json`
2. **Diff it** against the stored reference and users:
   `python3 -I scripts/diff_reference.py docs/seha-auth/permissions.json <scratch>/permissions-new.json DEV --users docs/seha-auth/users.json`
   It lists added, removed and re-numbered permissions, added, removed and changed roles, and roles with no entry in `users.json`, and ends with `ROLES_TO_CHECK=...`.
3. **Check only those roles**, in the stage the project is in:
   - seha stage: `read_sheet.py` on the new workbook, then `check.py --sheet ... --roles "<ROLES_TO_CHECK>"`, then `report.py seha ... --existing-users docs/seha-auth/users.json --merge` (keeps the other entries, replaces or adds the checked ones, drops roles removed from the sheet and lists them in the notes).
   - app stage: as above for any role new to `users.json` (it needs a seha-stage check first), then `check.py --users docs/seha-auth/users.json --roles "<ROLES_TO_CHECK>" --app-host ...` and `report.py app ...`.
4. **Replace the reference** once the user agrees: `build_reference.py "<new workbook>" docs/seha-auth/permissions.json --keep-app-mapping` (keeps the existing `appPermission` values; fill the new permissions' mapping).
5. Report the changes from the diff and the per-role results of the checked roles.

## The app mapping

`permissions.json` holds, per SEHA permission, `appPermission: { "value": <enum number>, "name": "<enum member>" }`, the app permission it maps to, or `null` when the app has no such permission. Fill it from the project, in this order:
1. the backend's mapping of SEHA permission IDs to its own permissions, if it has one (the source of truth once deployed);
2. otherwise the frontend's permission enum, matched by the permission label in the project's roles and permissions documents;
3. otherwise ask the user.
Show the user the filled mapping (or its changes) before relying on it. The app-mode check compares the app token against this file, so a wrong mapping here hides a wrong mapping in the backend.

## What to report

Always in chat, as a table per role, plus:
- the service metadata: Arabic and English name, the service URL (the app's domain) and Client ID of the environment, and the other environments' URLs from the reference;
- the result count (correct / with issues);
- notes: users with none of the sheet's roles, roles found under a different user than the sheet lists, organization mismatches (a role set up on another party's organization: fine on a test environment, to fix before production), and in update mode the list of changes;
- which files were written (`users.json`, `permissions.json`).

Ask before committing anything, and whether to delete the workbook once the reference and users JSON are written (it holds the client secret). Move it to the Trash rather than deleting it permanently.

## Issues met and how the scripts handle them

| Issue | Symptom | Handling |
|---|---|---|
| Invisible reCAPTCHA on SEHA's login page | The page spins forever after Login; no login request is sent | Wait about 6 s on the login page before submitting, with `viewport: null` as seha-auth does (`lib.mjs`). Never solve or bypass a CAPTCHA; if the wait stops helping, stop and tell the user |
| SEHA test environments are slow under load | `page.goto` timeouts with many browsers at once | 90 s page-load timeout, at most 3 users in parallel (`--parallel`), one retry per failed user or role |
| One SEHA account holds many roles | Selecting one role ends the other sessions of that account | Roles of one user run one after another; different users run in parallel |
| The app token is not there before the backend is deployed | No `token=` in the app iframe address, nothing in the app's storage | seha mode reads SEHA's own token instead: the `Authorization: Bearer` header of SEHA's API calls after the role is selected (or a JWT in SEHA's storage). `PermissionList` holds the role's SEHA permission IDs, `RoleId` the role |
| Role entries are free text | Account and organization names differ slightly from the sheet | The scripts list what SEHA shows and match roles by the Arabic role name (before " - "); `users.json` uses SEHA's exact texts |
| Service name spelling differs | The menu name differs from the sheet in hamza, alef or spacing | Arabic-insensitive comparison, then the closest name |
| Merged cells in "Test Users" | A role row shows no user because only the account and organization cells were merged with the row above | Such a row belongs to the user above |
| Permission labels with line breaks | "Prepare and submit COC1\nPrepare and submit C O C one" | Labels match on their first line |
| Two tabs on the role page | Business accounts (صحة أعمال) are on a second tab | Both tabs are listed; their entries get `"isBusiness": true` |
| Secrets in the workbook | Client Secret in "Services Profile" | Never read into any output; raw tokens never printed |

## Files

- `docs/seha-auth/users.json`: one entry per role (format in seha-auth Step 3), committed.
- `docs/seha-auth/permissions.json`: the reference, committed. Shape:
  ```json
  {
      "generatedFrom": "<workbook file name>",
      "generatedAt": "2026-11-08",
      "services": { "DEV": { "nameAr": "...", "nameEn": "...", "url": "https://...", "clientId": "..." } },
      "permissions": [
          { "en": "View claims", "ar": "عرض المطالبات", "level": "...", "sehaIds": { "DEV": 2359, "QA": null, "STG": null, "PROD": null },
            "appPermission": { "value": 10, "name": "ViewClaims" } }
      ],
      "roles": [ { "en": "Provider User", "ar": "مستخدم مزود الخدمة", "party": "", "permissions": ["View claims"] } ]
  }
  ```

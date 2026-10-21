---
name: db-test-setup
description: Snapshots and restores dev/test database data around a test, for any database engine, in two cases - (1) a scenario can't be reached with the data that exists (e.g. a request needs to be in a state no test account has), so the data is temporarily changed to set it up; (2) a test itself writes data (a reassign, a submit, a workflow step) and the database must be put back afterwards, even when no setup change is needed. Snapshot first, data changes only (never schema), restore in one transaction, verified against the snapshot. Use it from frontend-testing or backend-testing (or directly). Asks the user for the connection string; if they decline, the scenario is reported as blocked - needs data instead.
---

# DB Test Setup

Two modes:

-   **Setup and restore:** the scenario needs data that can't be created through the UI or API (a request at a specific stage, a field filled in, a role assigned). Change the data, run the test, put everything back.
-   **Restore only:** the test itself writes data (for example a reassign on dev). Make no setup change; snapshot what the test will write, then restore it.

Not for fixing data, migrations, seeding environments, or anything on production. If a change should outlive the test, it's not this skill's job.

The skill says _table_, _row_ and _column_; for document or key-value stores read _collection_, _document_ and _field_.

## Hard rules

1. **Never production.** Confirm the target is dev/test before the first write; ask if the server or database name doesn't make it obvious. If in doubt, stop.
2. **Data only, never schema.** Read, insert, update and delete records only. No structural, index, constraint, permission or server-setting changes, no admin commands, and never disable triggers, constraints or validators. Re-inserting records with their original ids (e.g. SQL Server's `SET IDENTITY_INSERT`) is allowed only inside a restore.
3. **Read before writing.** Inspect the rows, related tables and side effects with read-only queries first.
4. **Snapshot before the first write**: every row the setup _or the test_ may change, stored outside the repo and outside the generic scratchpad (step 3).
5. **Smallest change that unblocks the scenario.** One status update beats building data from scratch. In restore-only mode, no setup change at all.
6. **Restore in one transaction, then verify against the snapshot.** If the engine can't restore every affected record in one transaction, stop before the first write: **blocked - unsafe to proceed**.
7. **Credentials stay out of files, commits, logs and command-line arguments.** Pass them through a session-only environment variable.
8. **Ask, don't assume.** No connection string from the user means **blocked - needs data**. Never look for credentials in config files, `.env`, secret stores or shell history.

## Procedure

### 1. Connect

-   Ask for the connection string if you don't have it.
-   Detect the engine from the connection string; if it's unclear, ask. Read `references/engine-notes.md` for the engine-specific details before connecting.
-   Install a pinned client in the scratchpad, never globally and never inside the repo.
-   Connect read-only first and record the engine, version, server and database, and how you confirmed it is dev/test.

### 2. Plan

Using read-only queries:

-   Identify the scenario and its data precondition, if it needs one.
-   Identify every row the **test itself** is expected to write, including rows a workflow deletes and recreates with new ids (for example, child rows such as documents attached to a request).
-   Check triggers, cascades and generated values for extra writes.
-   **Confirm that one transaction can cover every affected record.** If it can't, stop here with **blocked - unsafe to proceed**.

Then write down: the tables and row ids (by primary key, never by display name), the original and intended values, the verification query, and the restore plan. If the target row is missing, ambiguous or belongs to someone else, ask or report the scenario as blocked.

### 3. Snapshot

Save every row from step 2, covering the setup change, the test's own writes, and anything triggers or cascades touch.

-   **Lossless, typed format.** It must keep exact datetime precision and time zone, exact decimals, binary data, nested/JSON values, and the difference between null, empty and missing. CSV, plain JSON and display strings usually don't; see `references/engine-notes.md` for formats that do.
-   Record whether each row existed before, so the restore knows what to delete.
-   **Round-trip check:** read the snapshot back and compare it with the live rows using typed comparison. Precision loss shows up here, often as datetime differences of a few milliseconds after a restore.
-   **Location:** always `~/.db-test-setup/snapshots/<yyyy-mm-dd>-<scenario-id>/`, readable only by the current user (`chmod 700`). Not the repo, not the scratchpad, not `/tmp`: the scratchpad and `/tmp` can be cleared mid-session. The first save to this folder may ask for permission; that's expected. Record the path; no credentials inside.

If any part fails, don't write.

### 4. Apply the setup change

Skip this step in restore-only mode.

Use a guarded update that only applies if the original value is still there, for example:

```sql
UPDATE TestRequests SET Status = @Temporary
WHERE RequestId = @Id AND Status = @Original;
```

Check that the affected-row count matches what you expect, read the row back, and confirm the precondition holds. If the count is unexpected, roll back and investigate.

### 5. Run the test

Hand control back to the calling skill (frontend-testing or backend-testing). **The calling skill reports pass/fail; this skill reports only on the data.** Keep the temporary state only as long as the test needs it. Restore even if the test fails or is abandoned.

### 6. Restore

Before restoring:

-   Confirm the snapshot is still there and readable.
-   Diff the current state against it.
-   Separate the changes the test is expected to make (restore them) from changes you can't explain. If restoring an unexplained change could overwrite someone else's work, stop and ask.

If the test changed a row that isn't in the snapshot, its original values are unknown. Don't guess them; leave the row and report the gap.

Then, in **one transaction**:

1. Put back modified and deleted rows, with their original ids.
2. Remove rows that didn't exist before.
3. Compare the result with the snapshot while still inside the transaction.
4. Commit only if it matches; otherwise roll back.

Use the snapshot as the only source of truth. If the connection drops, reconnect and inspect the actual state before doing anything else.

### 7. Verify

With fresh read-only queries, compare every row and column against the snapshot using typed comparison. Check that original ids are back, temporary rows are gone, and row counts match.

Any difference counts, including precision lost by the client. Record the table, row, column, expected and actual values. Don't attempt speculative repairs; report the difference and ask.

### 8. Report and clean up

Use one status:

-   **restored and verified**: the data matches the snapshot.
-   **restored with differences**: the restore completed, but something differs (list it).
-   **restore failed - intervention required**: the restore didn't complete or couldn't be verified.
-   **blocked - needs data**: no connection string, no environment confirmation, or the target rows couldn't be identified.
-   **blocked - unsafe to proceed**: the target might be production, the impact can't be bounded, there's no usable snapshot, or the engine can't restore atomically.

Include the environment and engine, the mode, the precondition, the rows changed, whether the restore ran in one transaction, and any differences. No credentials and no unnecessary personal data. Don't report test pass/fail.

Clean up temporary scripts, but keep the database client while the calling skill may still need it for read-only checks. Keep the snapshot until verification has passed. Make sure nothing was staged or committed.

## Done means

-   The target was confirmed as dev/test before the first write.
-   The snapshot covered both the setup change and the test's own writes, and passed the round-trip check.
-   The restore ran in one transaction.
-   The post-restore comparison against the snapshot passed, or every difference was reported.
-   No credentials ended up in any file, log or report.

A passing test without a verified restore is not a successful run of this skill.

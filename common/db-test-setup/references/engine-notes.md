# Database engine notes

Read this when connecting (step 1 of SKILL.md). It covers only what differs between engines or is easy to get wrong. Don't edit this file: it is synced from lean-ai-skills and local changes are overwritten. When you use an engine that has no section here, suggest a section to the user in your report instead.

## Any engine

-   **Identify the engine** from the connection string: its scheme (`postgresql://`, `mysql://`, `mongodb://`), driver name or parameters. Check the version once connected, because transaction support and types vary between versions. Never run one engine's syntax against another.
-   **Atomic restore support varies.** MySQL tables on a non-transactional storage engine such as MyISAM ignore transactions. MongoDB multi-document transactions need a replica set or sharded cluster. Check this before the first write (SKILL.md step 2).
-   **Implicit commits.** Some statements commit implicitly in some engines. Make sure nothing in the restore plan triggers one.
-   **Identity counters and sequences** usually advance even when a transaction rolls back. The restore puts the rows back, but not the counter.
-   **Writes can reach systems outside the database**, such as replicas, change streams, search indexes, caches or event consumers. A database restore doesn't undo those. Mention any you know of in the report.
-   **Certificates:** don't disable certificate validation just to get connected. Only do it in an explicitly approved dev/test configuration.
-   **localhost** may point to a container, a local instance, or nothing at all. Confirm it is the intended database.

## Snapshot formats

Use a typed export from the client library or the engine's own type-preserving format, for example MongoDB's canonical Extended JSON. Before the first write, check what the client returns for:

-   datetimes, including fractional seconds and time zone;
-   decimals, which must not come back as floats;
-   binary data;
-   nested and JSON values;
-   null versus empty versus missing.

## Re-inserting original ids

-   **SQL Server:** `SET IDENTITY_INSERT <table> ON`, for one table at a time, then `OFF` again.
-   **PostgreSQL:** `INSERT ... OVERRIDING SYSTEM VALUE` for `GENERATED ALWAYS` identity columns.
-   **MySQL:** explicit values can be inserted into `AUTO_INCREMENT` columns directly.

## SQL Server

-   **Authentication** can be SQL Server, Windows integrated or Microsoft Entra. Integrated and Entra may need an existing session, a supported driver or an explicit authentication setting.
-   **Connection strings** use semicolon-separated parameters. Escape special characters in passwords.
-   **Encryption:** newer drivers enable encryption by default. Use `TrustServerCertificate=True` only in an approved dev/test configuration.
-   **Transactions:** use `SET XACT_ABORT ON` plus `TRY...CATCH` (or the client's equivalent) so that any error rolls back.
-   **`GO`** is a client-side batch separator, not T-SQL. Many libraries reject it.
-   **Changed rows:** use `OUTPUT` or reliable row counts to confirm which rows changed.
-   **Parameter placeholders** depend on the client library (`@name`, `?`, `%s`).
-   **`datetime` columns** store time rounded to about 1/300 of a second. A client or snapshot format that doesn't preserve the stored value exactly will show small differences after a restore. Compare against the stored value, and report any difference that remains.

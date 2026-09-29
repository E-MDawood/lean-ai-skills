---
name: db-schema
description: Enterprise database standards for SQL Server — enforces all DBA rules when creating schemas, writing EF Core migrations, modifying tables, writing stored procedures, or writing C# data-access code. Covers table structure, naming, indexes, TVPs, archival, and deployment rules.
whenToUse: Activate for ANY of these: creating or modifying a table, writing or reviewing an EF Core migration, writing or modifying a stored procedure, writing C# code that calls a stored procedure (Dapper or EF), designing a database schema for a new project, reviewing SQL or migration files, adding columns or indexes, designing archival or lookup tables. Auto-apply whenever the task touches .sql files, Migrations/ folder, DbContext, stored procedure calls, or any database schema design.
---

# Enterprise Database Standards

> You are an enforcer of these standards, not just a reader.
> Before producing ANY database output — SQL, migrations, stored procedures, C# data-access code — run the relevant checklist at the bottom of this file. If a violation is found, **fix it** and explain why.
> If the user's request would violate a rule, **warn them first**, propose the compliant version, and only proceed if they confirm.

---

## SCENARIO QUICK LINKS

| What you are doing | Go to |
|---|---|
| Starting a new project / fresh schema | Section 1 |
| Creating or modifying a table | Section 2 + Section 3 |
| Writing an EF Core migration | Section 8 |
| Naming anything (table, column, SP, index) | Section 4 |
| Adding an index | Section 5 |
| Writing a stored procedure | Section 6 |
| Passing a list of IDs to a stored procedure | Section 7 |
| Designing archival or log tables | Section 9 |
| Making a change to an existing schema | Section 10 |

---

## 1. New Project / Schema Bootstrap

When starting a fresh database schema or a new project, follow this sequence before writing any table:

1. **Confirm an ERD exists and has been reviewed and approved** before writing any table definition. If no ERD exists, ask the user to provide or sketch one before proceeding.
2. **Identify archival strategy upfront** — for every table that will grow unbounded (logs, history, events), decide whether it is a Hot archive (queryable, stays in SQL Server) or Cold archive (offloaded, periodic clear). Document this decision as a comment in the migration.
3. **Create the `[dbo].[IntList]` TVP type** as the very first migration step if stored procedures will receive lists of IDs. This type must exist before any SP that uses it.
4. **Set up lookup schemas** — create a `lookup` schema for all lookup/reference tables before adding business tables.
5. **Plan mandatory columns for every table** — every single table, including join tables, must have `Id`, `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy` from day one. Never add these retroactively.

---

## 2. Mandatory Table Structure

Every table — including many-to-many join tables — **must** include these five columns. No exceptions.

| Column | Type | Constraint | Notes |
|---|---|---|---|
| `Id` | `int` | `IDENTITY(1,1) PRIMARY KEY` | Never use composite PK — convert to UNIQUE constraint |
| `CreatedAt` | `datetime2(7)` | `NOT NULL` | Set on insert, never modified after |
| `UpdatedAt` | `datetime2(7)` | `NOT NULL` | **Initially set to the same value as `CreatedAt`**, then updated on every row change |
| `CreatedBy` | `int` | `NOT NULL`, FK to Users table | Must be a proper foreign key — never a plain `int` with no FK |
| `UpdatedBy` | `int` | `NOT NULL`, FK to Users table | Must be a proper foreign key — never a plain `int` with no FK |

### Composite PKs must become UNIQUE constraints

If the original design has a composite primary key, replace it with a single `Id` column and a `UNIQUE` constraint on the original column set:

```sql
-- Wrong
PRIMARY KEY (UserId, RoleId)

-- Correct
Id    INT IDENTITY(1,1) NOT NULL,
CONSTRAINT PK_UserRole               PRIMARY KEY (Id),
CONSTRAINT UQ_UserRole_UserId_RoleId UNIQUE (UserId, RoleId)
```

### Essential business columns must be NOT NULL

Columns that represent critical business data must **never** be nullable. This includes:

- National ID / Civil ID
- Date of Birth (`DOB_H`, `DOB_G`)
- First name, last name (in any language variant)
- Any other column the business considers essential for data quality

If the data is not available at insert time, block the insert — do not allow `NULL` as a shortcut.

---

## 3. Data Types & Column Rules

### Strict rules — no exceptions

- **No `NVARCHAR(MAX)`, `VARCHAR(MAX)`, or `VARBINARY(MAX)`** — always choose an explicit, justified length.
- **Use `NVARCHAR` for all text columns** — supports Arabic and internationalization. Never use `VARCHAR` for business data.
- **All ID columns must be `int`**, including `RoleId`, `UserId`, `EmployeeId`, and every other FK reference. Never use `bigint` for ID columns, never use `uniqueidentifier` / UUID.
- **Use `bigint`** only for large or high-volume tables where the numeric range of `int` will be exceeded — and only for the `Id` column of that specific table, not for FK references to it.
- **Use `IDENTITY`** for auto-incrementing columns — never use sequences.
- **Numeric values must use numeric data types** (`int`, `bigint`, `decimal`, `float`) — never store a number as `NVARCHAR` unless there is a strong documented reason.
- **Do not store files** (images, PDFs, binary logs, JSON blobs) in the database.
- **Max 30 columns per table** — flag any table that reaches or exceeds this limit and recommend refactoring.

### Standard column formats

| Column | Type | Values / Notes |
|---|---|---|
| Gender | `CHAR(1)` | `'M'` or `'F'` only |
| Email | `NVARCHAR(50)` | Column must be named `Email` |
| Hijri date | `NVARCHAR` or `DATE` | Suffix `_H`, e.g. `DOB_H` |
| Gregorian date | `DATE` or `datetime2(7)` | Suffix `_G`, e.g. `DOB_G` |
| Multi-language text | `NVARCHAR(n)` | Language suffix: `FirstNameAr`, `FirstNameEn` |

### Reserved SQL keywords — banned as column names

Never use SQL Server reserved keywords as column names. Common traps:

`Type`, `Value`, `Key`, `Date`, `Time`, `Level`, `Status`, `Name`, `Order`, `User`, `Table`, `Index`, `View`, `Row`, `Column`, `Group`, `Select`, `From`, `Where`

If the user requests one of these as a column name, warn them and suggest a domain-specific alternative (e.g., `StatusCode`, `EntityType`, `RequestLevel`).

---

## 4. Naming Conventions

| Object | Convention | Example |
|---|---|---|
| Tables | PascalCase, **singular** | `Employee`, `WorkOrder`, `UserRole` |
| Columns | PascalCase | `FirstName`, `CreatedAt`, `NationalId` |
| Multi-language columns | Language suffix | `FirstNameAr`, `FirstNameEn` |
| Hijri date columns | `_H` suffix | `DOB_H` |
| Gregorian date columns | `_G` suffix | `DOB_G` |
| Views | `v_` prefix | `v_ActiveEmployees` |
| Functions | `fn_` prefix | `fn_CalculateSalary` |
| Stored Procedures | `usp_` prefix, PascalCase verb-noun | `usp_GetEmployeeById`, `usp_CreateWorkOrder` |
| Unique constraints | `UQ_[Table]_[Column]` | `UQ_Employee_NationalId` |
| Foreign keys | `FK_[Table]_[Column]` | `FK_WorkOrder_EmployeeId` |
| Indexes | `IX_` prefix | `IX_Employee_Email` |
| Lookup tables | `lookup.` schema | `lookup.EmployeeType`, `lookup.Gender` |

### Index naming — EF Core special note

**Do not write index names manually in EF Core migrations.** EF Core generates `IX_`-prefixed names by default — this is the correct behavior and matches the required standard. Only name an index manually if EF does not generate one (e.g., a raw SQL index in a migration `Up()` method). If you do write one manually, always follow the `IX_[Table]_[Column]` format.

---

## 5. Indexes & Constraints

### When to add an index

- **Non-clustered indexes should be avoided unless there is a justified performance need.** Do not add indexes pre-emptively.
- Before suggesting a new index, always recommend the user **inspect the execution plan** for the specific query. Look for scans vs. seeks, costly sorts, and hash joins. Re-check the plan after adding the index.
- Every **foreign key column** that participates in frequent joins should have an index — this is one of the most commonly missed optimizations.

### Index caps and cost awareness

- Hard cap: **5–7 non-clustered indexes** per table maximum. Beyond this, justify with measured performance data and periodically review and drop unused indexes.
- Every index slows `INSERT`, `UPDATE`, and `DELETE`. Always benchmark write-heavy tables before adding indexes.

### Composite index rules

- **Max 3 key columns** in a composite index. If more columns are needed to cover the query, add them as `INCLUDE` columns — not as additional key columns.
- Column order in a composite index must follow this left-to-right sequence:
  1. Equality predicates (`=`)
  2. Range predicates (`>`, `<`, `BETWEEN`, `>=`, `<=`)
  3. `ORDER BY` / `GROUP BY` columns

```sql
-- Filter by Status (equality), range on CreatedAt, cover Name columns
CREATE INDEX IX_Employee_Status_CreatedAt
ON Employee (Status, CreatedAt)
INCLUDE (FirstNameAr, FirstNameEn);
```

### Other index rules

- Use `UNIQUE` indexes when a business rule enforces uniqueness — they improve query plans and prevent duplicate data.
- Use **filtered indexes** for partial predicates (e.g., `WHERE IsActive = 1`) — they are smaller and more selective than full indexes.
- Do not index `NVARCHAR(MAX)`, JSON, XML, or large LOB columns.
- Low-cardinality columns (boolean, status with 2–3 values) should not be indexed alone — combine with a more selective column.
- **Max 5 foreign keys per table.**

---

## 6. Stored Procedures

### Mandatory structure

Every stored procedure must begin with `SET NOCOUNT ON` inside the `BEGIN` block — no exceptions:

```sql
CREATE PROCEDURE [schema].[usp_ProcedureName]
    @Param1 DataType
AS
BEGIN
    SET NOCOUNT ON;

    -- procedure body
END
```

### Rules

- `SET NOCOUNT ON` is **mandatory** — suppresses unnecessary rowcount messages sent to the client.
- **No triggers** — banned entirely for performance and maintainability reasons.
- **No dynamic SQL** unless absolutely necessary. If unavoidable, use `sp_executesql` with parameterized queries. Never concatenate user input into a SQL string.
- Return **only the columns the caller needs** — never `SELECT *`.
- **Use transactions** for any operation that touches more than one table and must be atomic. Always pair with `TRY/CATCH` and rollback:

```sql
BEGIN TRY
    BEGIN TRANSACTION;

    -- multi-table operations here

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    THROW;
END CATCH
```

- Write queries in a **set-based manner** — never use cursors or row-by-row loops unless absolutely unavoidable and documented.
- `ORDER BY` must always be `ORDER BY [Alias].Id DESC`. Never order by `CreatedAt` or `UpdatedAt`.

---

## 7. TVP — Passing Lists of IDs

> **Auto-warn rule:** If you see a comma-separated `NVARCHAR` string being passed to a stored procedure to represent a list of IDs, immediately flag it as a standards violation and provide the TVP replacement shown below.

**Never pass a list of IDs as a comma-separated `NVARCHAR` string.** Use Table-Valued Parameters (TVPs) instead.

### Why the NVARCHAR approach is wrong

| Problem | Detail |
|---|---|
| Type unsafe | Requires `TRY_CAST` on every row |
| Performance hit | `STRING_SPLIT` runs on every execution |
| SQL injection risk | String input is always dangerous |
| NULL handling confusion | `IS NULL` check works but is fragile |

### Step 1 — Create the TVP type (once per database, in the first migration)

```sql
CREATE TYPE [dbo].[IntList] AS TABLE
(
    Id INT NOT NULL,
    PRIMARY KEY (Id)  -- prevents duplicates and enables fast lookup
);
```

> **UDT exception:** The enterprise standards restrict User-Defined Types (UDTs). `[dbo].[IntList]` is the **one allowed exception** — it is required for the TVP pattern and must be created in every database that uses stored procedures with list-of-ID parameters. All other UDTs remain forbidden.

### Step 2 — Stored procedure parameter declaration

```sql
CREATE PROCEDURE [api].[usp_FetchEntity]
    @FilterIds [dbo].[IntList] READONLY  -- READONLY is mandatory; SP will not compile without it
AS
BEGIN
    SET NOCOUNT ON;

    SELECT E.Id, E.Name, E.ParentId
    FROM [dbo].[Entity] E
    WHERE NOT EXISTS (SELECT 1 FROM @FilterIds)  -- empty TVP = no filter = return all rows
       OR EXISTS (
           SELECT 1
           FROM @FilterIds F
           WHERE F.Id = E.ParentId  -- direct int comparison, no cast needed
       );
END
```

**Key rules:**

- `READONLY` is **mandatory** — SQL Server requires it on all TVP parameters. The SP will not compile without it.
- `NOT EXISTS (SELECT 1 FROM @FilterIds)` replaces `@param IS NULL`. A TVP **cannot be NULL** — an empty table means "no filter applied, return everything".
- Never use `IS NULL` to check whether a TVP was populated.

### Step 3 — C# reusable helper (create once per project, reuse everywhere)

```csharp
public static class TvpHelper
{
    public static SqlParameter ToIntListTvp(
        this IEnumerable<int> ids,
        string paramName = "@FilterIds")
    {
        var table = new DataTable();
        table.Columns.Add("Id", typeof(int)); // column name must exactly match the SQL type definition

        foreach (var id in ids)
            table.Rows.Add(id);

        return new SqlParameter(paramName, SqlDbType.Structured) // SqlDbType.Structured is required
        {
            TypeName = "dbo.IntList", // must exactly match the SQL type name (schema.TypeName)
            Value = table
        };
    }
}
```

**Critical C# rules:**

- `SqlDbType.Structured` is **required** — without it Dapper cannot map the `DataTable` to the TVP.
- `TypeName = "dbo.IntList"` must exactly match the SQL type name — schema, casing, and name.
- The `DataTable` column name `"Id"` must exactly match the column defined in the SQL type (`Id INT NOT NULL`).

### Step 4 — Dapper call with a populated list

```csharp
var ids = new List<int> { 1, 2, 3 };

var result = await connection.QueryAsync<Entity>(
    "api.usp_FetchEntity",
    new { FilterIds = ids.ToIntListTvp() },
    commandType: CommandType.StoredProcedure
);
```

### Step 5 — Passing an empty list (return all records)

```csharp
// Empty list = no filter = returns all records (handled by NOT EXISTS in the SP)
var ids = new List<int>();

var result = await connection.QueryAsync<Entity>(
    "api.usp_FetchEntity",
    new { FilterIds = ids.ToIntListTvp() },
    commandType: CommandType.StoredProcedure
);
```

### Before vs. after summary

| | Old (NVARCHAR) | New (TVP) |
|---|---|---|
| SQL parameter | `'1,2,3'` string | Typed `IntList` table |
| Type safety | Needs `TRY_CAST` | Already `INT` |
| Performance | `STRING_SPLIT` on every call | Indexed table lookup |
| Empty = return all | Must pass `NULL` | Pass empty list |
| SQL injection | Possible | None |
| Dapper call | Plain string param | `SqlParameter` + Structured type |
| Reusable helper | None | `.ToIntListTvp()` extension |

---

## 8. EF Core / Migrations

- **Never name indexes manually** in EF Core fluent configuration unless EF does not generate one automatically. EF Core default `IX_[Table]_[Column]` naming is the required standard — do not override with `.HasDatabaseName(...)` unless absolutely necessary.
- Every migration that creates a table must include all five mandatory columns: `Id`, `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy`.
- The `UpdatedAt` column default must be set equal to `CreatedAt` for new rows:

```csharp
table.Column<DateTime>(name: "UpdatedAt", type: "datetime2(7)", nullable: false,
    defaultValueSql: "GETUTCDATE()")
```

- When writing raw SQL in `Up()` (stored procedures, TVP types, views), always include the corresponding `Down()` that reverses it.
- Include a **rollback plan** comment on any migration with a destructive or hard-to-reverse change:

```csharp
// ROLLBACK PLAN: run Down() or manually execute: DROP TABLE [dbo].[TableName]
```

- Entity ID properties must be `int`. Never use `Guid` or `long` for entity IDs unless the table is explicitly classified as high-volume.

---

## 9. Archival & History Data

- **Do not create audit, error, request, or response tables** in SQL Server.
- **Do not create SQL Agent jobs.**
- For history and log data, use **MongoDB** — or design the table for periodic clear/archive.
- Every table that can grow unbounded must be classified as one of:
  - **Hot archive** — stays in SQL Server, queryable, with a defined retention period and cleanup strategy.
  - **Cold archive** — periodically offloaded or cleared; the SQL table is a staging area only.
- The classification and retention period must be documented as a comment in the migration or schema design.

---

## 10. Schema Changes & Deployment Rules

### Hard restrictions on existing tables

| Operation | Status | Safe alternative |
|---|---|---|
| Renaming a column | **Not allowed** | Add new column, migrate data, deprecate old column in a later migration |
| Changing a column data type | **Not allowed** | Add new column with correct type, migrate data, drop old column after all consumers updated |
| Adding a NOT NULL column with no default to a non-empty table | **Not allowed** | Provide a `DEFAULT` value or make it nullable initially |

If the user requests a rename or type change, warn them and describe the safe alternative above.

### Deployment requirements

- Every deployment that modifies the database **must have a rollback plan** — either a `Down()` migration or a documented manual rollback script.
- Multi-statement migrations must follow ACID principles — wrap in a transaction where SQL Server allows it.
- If a migration touches a table consumed by other services, note those services in a comment in the migration.

---

## 11. Schema Organization & Design Principles

- Use dedicated schemas: business tables in `dbo.` or a domain schema (`api.`, `hr.`), lookup/reference tables in `lookup.`.
- Each distinct lookup concept gets its own table: `lookup.EmployeeType`, `lookup.Gender`, `lookup.Department`. Do not combine multiple lookup types into a single generic table.
- Normalize to at least **3NF** (Third Normal Form) — every non-key column must depend on the whole primary key and nothing else.
- Databases must follow **ACID** principles — atomicity, consistency, isolation, durability.
- Write all queries in a **set-based manner** — avoid cursors and row-by-row processing.
- Return only the data the caller needs — do not over-fetch.

---

## 12. Pre-Output Checklists

Run the relevant checklist before producing output. Fix every failing item first.

---

### Checklist A — New table (migration or raw SQL)

- [ ] Has `Id INT IDENTITY(1,1) PRIMARY KEY`
- [ ] Has `CreatedAt datetime2(7) NOT NULL`
- [ ] Has `UpdatedAt datetime2(7) NOT NULL` — default equals `CreatedAt`
- [ ] Has `CreatedBy int NOT NULL` with a foreign key constraint
- [ ] Has `UpdatedBy int NOT NULL` with a foreign key constraint
- [ ] No composite primary key (converted to UNIQUE constraint)
- [ ] No reserved SQL keywords used as column names
- [ ] Column count is 30 or fewer
- [ ] No `NVARCHAR(MAX)` / `VARCHAR(MAX)` / `VARBINARY(MAX)`
- [ ] All text columns use `NVARCHAR`
- [ ] All numeric/monetary values use numeric data types (not `NVARCHAR`)
- [ ] All ID/FK columns are `int` (not `bigint`, not `uniqueidentifier`)
- [ ] Essential business columns (NationalId, DOB, Names) are `NOT NULL`
- [ ] FK count is 5 or fewer
- [ ] Table name is PascalCase, singular
- [ ] Column names are PascalCase
- [ ] In `lookup` schema if it is a reference/lookup table
- [ ] Archival strategy defined if the table can grow unbounded

---

### Checklist B — EF Core migration

- [ ] All five mandatory columns present on every new table
- [ ] No index named manually (rely on EF default `IX_` naming)
- [ ] `Down()` method correctly reverses all `Up()` changes
- [ ] Rollback plan comment added for destructive changes
- [ ] `[dbo].[IntList]` TVP type created before any SP that uses it
- [ ] No column renames or data type changes on existing tables
- [ ] Entity ID properties are `int`

---

### Checklist C — Stored procedure

- [ ] `SET NOCOUNT ON;` is the first statement inside `BEGIN`
- [ ] SP name uses `usp_` prefix, PascalCase
- [ ] No triggers
- [ ] No dynamic SQL (or justified and using `sp_executesql` with parameters)
- [ ] Multi-table operations wrapped in `TRY/CATCH` with transaction and rollback
- [ ] `SELECT` returns only required columns — no `SELECT *`
- [ ] `ORDER BY Id DESC` (not `CreatedAt`, not `UpdatedAt`)
- [ ] Queries are set-based, no cursors
- [ ] List-of-IDs parameter uses `[dbo].[IntList] READONLY` — never `NVARCHAR(MAX)`

---

### Checklist D — C# data-access code (Dapper / EF)

- [ ] No comma-separated string being passed as a list of IDs
- [ ] List-of-IDs uses `.ToIntListTvp()` extension method
- [ ] `SqlParameter` uses `SqlDbType.Structured` and `TypeName = "dbo.IntList"`
- [ ] `DataTable` column name matches SQL type column name exactly (`"Id"`)
- [ ] Empty list (`new List<int>()`) correctly means "return all" — no null check that would break this

---

### Checklist E — Schema change on existing table

- [ ] No column renames (propose the add-new-column-then-deprecate approach instead)
- [ ] No data type changes (propose the add-new-column approach instead)
- [ ] Rollback plan documented
- [ ] Any new NOT NULL column has a default value, or the table is confirmed empty
- [ ] Affected downstream services/consumers identified in a migration comment
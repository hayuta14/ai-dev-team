---
name: database-migrations
description: Use when writing, reviewing, or planning the rollout of a PostgreSQL schema or data migration on a table that already holds data - adding or changing columns, NOT NULL, indexes, foreign keys, renames, drops, or backfills - so the change does not lock the table, fail halfway, or break the app version still running during deploy. Covers lock_timeout, expand-contract, CREATE INDEX CONCURRENTLY, NOT VALID constraints, and batched backfills. Triggers (VI): "viết migration", "đổi tên cột", "thêm cột NOT NULL", "backfill dữ liệu", "migration có khoá bảng không".
license: MIT — derived from github.com/affaan-m/ECC skills/database-migrations (Affaan Mustafa), rewritten for team-ai-pack with every Postgres claim re-measured on Postgres 16. See LICENSE.txt.
---

# Database migrations (PostgreSQL)

A migration is safe when three things hold: it does not hold a strong lock long enough to stall traffic, it cannot leave the schema half-applied, and the app version that is still running during the deploy keeps working against the new schema. Everything below serves one of those three.

Schema design, RLS, indexes as query tuning: `supabase-postgres-best-practices`. This skill is the procedure for changing a schema that already has rows and users.

## Rules

1. **Every change is a migration file in the repo.** No hand-run SQL on a shared database. Run it the way the repo documents (README, CLAUDE.md); running it on a shared database is `database-admin`'s seat with an approved step.
2. **Forward-only once deployed.** Never edit a migration that has run anywhere shared; fix with a new migration. A "down" file is a plan, not a guarantee: dropped data does not come back.
3. **Schema (DDL) and data (DML) in separate migrations.** A backfill inside a DDL transaction holds the DDL's lock for the whole backfill.
4. **Old app, new schema.** During a rolling deploy the previous image still serves traffic. Every migration must be readable and writable by both the old and the new app version, or the deploy is split (see expand-contract).
5. **Set `lock_timeout` on every DDL against a live table.** See below; this is the rule people skip.

## Why lock_timeout (measured)

`ALTER TABLE` needs an `ACCESS EXCLUSIVE` lock. While it waits for a long-running transaction to finish, every new query on that table, plain `SELECT` included, queues behind it. Measured on Postgres 16: a reader holds the table, an `ALTER TABLE ... ADD COLUMN` waits, and a third session's `SELECT count(*)` hit its 2 s `statement_timeout` without running. A fast DDL becomes an outage because of the wait, not the work.

```sql
SET lock_timeout = '5s';        -- give up instead of stalling the table; retry later
SET statement_timeout = '15min'; -- optional ceiling for the statement itself
ALTER TABLE orders ADD COLUMN note text;
```

A failed attempt prints `canceling statement due to lock timeout`; retry, or find the blocker in `pg_stat_activity`.

## What rewrites or scans the table (Postgres 16, 200k rows; rows marked *doc* are from the Postgres docs, not measured here)

| Change | Effect | Safe form |
|---|---|---|
| `ADD COLUMN x text` (nullable, no default) | metadata only | as is |
| `ADD COLUMN x boolean NOT NULL DEFAULT true` (constant) | metadata only (PG ≥ 11) | as is |
| `ADD COLUMN x timestamptz NOT NULL DEFAULT now()` | metadata only (`now()` evaluated once) | as is |
| `ADD COLUMN x uuid DEFAULT gen_random_uuid()` (volatile default) | **full table rewrite** | add nullable, backfill in batches, then default + NOT NULL |
| `ADD COLUMN x text NOT NULL` with no default, table has rows | **fails**: `column "x" ... contains null values` | add nullable, backfill, then NOT NULL |
| `ALTER COLUMN n TYPE bigint` (from `int`) | **full table rewrite** | new column + backfill + swap (expand-contract) |
| `varchar(50)` → `varchar(100)`, `varchar` → `text` | metadata only | as is |
| `ALTER COLUMN x SET NOT NULL` | full scan under `ACCESS EXCLUSIVE` *doc* | `CHECK (x IS NOT NULL) NOT VALID` → `VALIDATE CONSTRAINT` → `SET NOT NULL` (PG ≥ 12 skips the scan; measured: `DEBUG: existing constraints ... sufficient to prove that it does not contain nulls`) |
| `ADD FOREIGN KEY` | scans the table under a lock *doc* | `... NOT VALID`, then `VALIDATE CONSTRAINT` in a later statement |
| `CREATE INDEX` | blocks writes for the whole build *doc* | `CREATE INDEX CONCURRENTLY` |

Verify a rewrite on a copy yourself: `select pg_relation_filenode('t');` before and after; a different number means the table was rewritten.

## Transactions: what cannot run inside one

- `CREATE INDEX CONCURRENTLY` / `DROP INDEX CONCURRENTLY` fail inside a transaction block (`cannot run inside a transaction block`).
- A `DO $$ ... COMMIT ... $$` batch loop fails inside a transaction (`invalid transaction termination`). It also fails when the file is sent as **one multi-statement query string** (measured with `psql -c '<two statements>'`), because that string runs as one implicit transaction.

Before relying on either, find out how the repo's runner sends the file: per statement, one transaction per file, or one query string. If you cannot tell, put the concurrent index or the batch loop in its own file and run it as a separate step, and say so in the plan.

## Patterns

**NOT NULL on an existing column**

```sql
-- migration 1 (DDL)
SET lock_timeout = '5s';
ALTER TABLE users ADD CONSTRAINT users_email_not_null CHECK (email IS NOT NULL) NOT VALID;
-- migration 2 (after any backfill)
ALTER TABLE users VALIDATE CONSTRAINT users_email_not_null;  -- weaker lock, scans
SET lock_timeout = '5s';
ALTER TABLE users ALTER COLUMN email SET NOT NULL;             -- uses the validated check, no scan
ALTER TABLE users DROP CONSTRAINT users_email_not_null;
```

**Batched backfill** (its own step, outside a transaction, or driven from a script one batch per transaction)

```sql
DO $$
DECLARE n int;
BEGIN
  LOOP
    UPDATE users SET email_normalized = lower(email)
    WHERE id IN (SELECT id FROM users WHERE email_normalized IS NULL LIMIT 10000 FOR UPDATE SKIP LOCKED);
    GET DIAGNOSTICS n = ROW_COUNT;
    EXIT WHEN n = 0;
    COMMIT;
  END LOOP;
END $$;
```

The `WHERE ... IS NULL` makes it resumable: a rerun after a failure continues where it stopped.

**Rename or retype a column (expand-contract)**: never `RENAME COLUMN` while the old app still reads the old name.

1. Expand: add the new column (nullable). Deploy app that writes both columns (or a trigger that copies).
2. Backfill old rows in batches.
3. Switch: deploy app that reads the new column, still writes both.
4. Contract: deploy app that stops using the old column; in a later migration, drop it.

Each step is its own deploy; the plan lists them as separate phases with their own rollback.

**Drop a column or table**: remove every code reference first, deploy, then drop in the next migration. Dropping first breaks the running old version.

## Checklist before the migration ships

- [ ] `lock_timeout` set before each DDL on a table with traffic.
- [ ] No row in the table above that rewrites or scans a large table without its safe form.
- [ ] DDL and backfill in separate migrations; backfill batched and resumable.
- [ ] `CONCURRENTLY` / batch loops not inside a transaction the runner opens.
- [ ] Old app version works against the new schema (or the change is split).
- [ ] New table: RLS or a written reason (`supabase-postgres-best-practices`).
- [ ] Rollback written down: which statement undoes it, and which steps cannot be undone (data dropped, type narrowed).
- [ ] Tried on a copy with realistic row counts when the table is large; timing noted.

## Report back

State, per migration file: what it locks and for how long you expect, whether it rewrites, whether the old app keeps working, and its rollback. "Not measured" is an acceptable answer; a guess presented as a measurement is not.

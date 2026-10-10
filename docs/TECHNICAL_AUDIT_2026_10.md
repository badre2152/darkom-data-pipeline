# Technical Audit

## Scope

This audit inspected the pipeline entry point, PostgreSQL connection helper, migration code, and staging load. Other transformation and warehouse behavior, the Power BI binary, and database results still require integration testing.

## Confirmed findings

### High: unsafe manual PostgreSQL URL construction

`src/utils/db.py` constructed a SQLAlchemy connection URL by interpolating raw credentials. Characters such as `@`, `/`, `:`, and `?` can change URL parsing and prevent valid database logins. It now uses `sqlalchemy.URL.create` to preserve credentials.

### Medium: unvalidated connection search path

The same function accepted arbitrary `schema` values and put them into libpq connection options. A fixed allowlist now limits values to the five schemas used by this project.

### High: staging replacement was non-atomic

`src/staging/load_staging.py` truncates `bronze.stg_annonces` in one committed transaction and performs `DataFrame.to_sql` afterwards. If insertion fails, the previously loaded staging data have already been removed. The staging TRUNCATE, insertion, and success audit entry now share one transaction. A PostgreSQL rollback regression test has been added, pending CI execution.

### Medium: logging and documentation cleanup remains open

Several modules contain decorative banner logs, overlong historical change notes, and explanatory comments. Removing those must not alter Python indentation, SQL semantics, or audit signal.

## Verification

Connection URL tests mock SQLAlchemy. Staging rollback is now exercised against a PostgreSQL 16 CI service. A successful CI result is required; full Silver/Gold pipeline and Power BI report correctness remain unverified. Full pipeline execution has not been confirmed.

## Recommended next checks

1. Pass CI on the audit branch.
2. Verify the transactional staging import and rollback test against PostgreSQL in CI.
3. Validate Silver and Gold steps on a known synthetic fixture.
4. Inspect reference DAX and report metadata before claiming current model performance.

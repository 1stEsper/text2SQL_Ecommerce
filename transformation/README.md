# Transformation

This dbt project transforms the raw `bronze` tables loaded by dlt into:

- `silver`: cleaned and deduplicated views
- `gold`: dimensional tables, a sales fact table, and business marts

## Run the project

Close any notebook or DuckDB CLI connection that has the database open, then run:

```bash
cd transformation
uv run dbt build --profiles-dir .
```

The default DuckDB database is `../ingestion/medallion.duckdb`. Override it when
needed with the `T2S_DUCKDB_PATH` environment variable.

Useful commands:

```bash
uv run dbt build --profiles-dir . --select silver
uv run dbt build --profiles-dir . --select gold
uv run dbt test --profiles-dir .
```

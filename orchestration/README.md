# Airflow and Cosmos orchestration

This local Docker deployment runs the complete batch pipeline:

1. dlt replaces the four bronze tables from SQL Server.
2. Cosmos renders the dbt project as individual Airflow tasks.
3. dbt builds and tests the silver, gold, and marts models.

The Streamlit dashboard and Gemini text-to-SQL application remain interactive
services and are not started by this DAG.

## First run

From the repository root, copy and complete the environment template:

```bash
cp .env.example .env
```

At minimum, set all `SQL_SERVER_*` values. Set your host user ID so containers
can write the DuckDB file and Airflow logs:

```bash
export AIRFLOW_UID="$(id -u)"
docker compose -f orchestration/docker-compose.yml build
docker compose -f orchestration/docker-compose.yml up airflow-init
docker compose -f orchestration/docker-compose.yml up -d
```

Open <http://localhost:8080>, sign in with the `AIRFLOW_ADMIN_*` values, enable
`ecommerce_medallion_pipeline`, and trigger it. The default schedule is daily at
06:00 UTC.

To inspect logs:

```bash
docker compose -f orchestration/docker-compose.yml logs -f airflow-scheduler
```

To stop services without deleting the Airflow metadata database:

```bash
docker compose -f orchestration/docker-compose.yml down
```

Add `--volumes` only when you intentionally want to delete Airflow's local
metadata database and start over.

## DuckDB concurrency

All write tasks use the single-slot `duckdb_writer` Airflow pool, and the DAG
allows only one active task and one active run. This is deliberate: separate
processes must not write to the same DuckDB file concurrently.

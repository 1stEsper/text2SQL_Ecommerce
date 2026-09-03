"""Orchestrate SQL Server ingestion and the dbt medallion transformations."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pendulum
from airflow.sdk import DAG, task
from cosmos import (
    DbtTaskGroup,
    ExecutionConfig,
    ProfileConfig,
    ProjectConfig,
    RenderConfig,
)
from cosmos.constants import ExecutionMode, LoadMode, TestBehavior


PROJECT_ROOT = Path(os.getenv("T2S_PROJECT_ROOT", "/opt/airflow/project"))
DBT_PROJECT_PATH = PROJECT_ROOT / "transformation"
DUCKDB_PATH = Path(
    os.getenv(
        "T2S_DUCKDB_PATH",
        str(PROJECT_ROOT / "ingestion" / "medallion.duckdb"),
    )
)


with DAG(
    dag_id="ecommerce_medallion_pipeline",
    description="Load bronze data and build dbt silver, gold, and marts models.",
    schedule="0 6 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    default_args={"retries": 2},
    tags=["ecommerce", "dlt", "dbt", "duckdb"],
) as dag:

    @task(pool="duckdb_writer")
    def ingest_bronze() -> None:
        """Run the existing dlt ingestion with a deterministic database path."""
        environment = os.environ.copy()
        environment["T2S_DUCKDB_PATH"] = str(DUCKDB_PATH)

        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "ingestion" / "ingest.py")],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
        )

    dbt_transform = DbtTaskGroup(
        group_id="dbt_transform",
        project_config=ProjectConfig(
            dbt_project_path=str(DBT_PROJECT_PATH),
        ),
        profile_config=ProfileConfig(
            profile_name="transformation",
            target_name="dev",
            profiles_yml_filepath=str(DBT_PROJECT_PATH / "profiles.yml"),
        ),
        execution_config=ExecutionConfig(
            execution_mode=ExecutionMode.LOCAL,
        ),
        render_config=RenderConfig(
            load_method=LoadMode.DBT_LS,
            test_behavior=TestBehavior.AFTER_EACH,
        ),
        operator_args={
            "pool": "duckdb_writer",
            "env": {"T2S_DUCKDB_PATH": str(DUCKDB_PATH)},
        },
    )

    ingest_bronze() >> dbt_transform

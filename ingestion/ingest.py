import os
from pathlib import Path

import dlt
from dotenv import load_dotenv
from dlt.sources.credentials import ConnectionStringCredentials
from dlt.sources.sql_database import sql_database
from sqlalchemy.engine import URL

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DUCKDB_PATH = PROJECT_ROOT / "ingestion" / "medallion.duckdb"


def require_env(name: str) -> str:
    """Return a required environment variable or fail with a clear message."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} has not been configured in the .env file!")
    return value


def get_duckdb_path() -> Path:
    """Return one absolute DuckDB path shared by ingestion and dbt."""
    configured_path = os.getenv("T2S_DUCKDB_PATH")
    return Path(configured_path or DEFAULT_DUCKDB_PATH).expanduser().resolve()


def create_source():
    connection_url = URL.create(
        "mssql+pyodbc",
        username=require_env("SQL_SERVER_USER"),
        password=require_env("SQL_SERVER_PASSWORD"),
        host=require_env("SQL_SERVER_HOST"),
        port=int(os.getenv("SQL_SERVER_PORT", "1433")),
        database=require_env("SQL_SERVER_DATABASE"),
        query={
            "driver": os.getenv(
                "SQL_SERVER_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"
            ),
            "TrustServerCertificate": "yes",
        },
    )

    credentials = ConnectionStringCredentials(
        connection_url.render_as_string(hide_password=False)
    )
    return sql_database(
        credentials,
        schema="e_commerce",
        table_names=["customer", "ecom_sales", "product", "region"],
    )


def main():
    print("Trying to connect SQL Server ...")

    source = create_source()
    duckdb_path = get_duckdb_path()
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = dlt.pipeline(
        pipeline_name="xomdata_sqlserver_ingest",
        destination=dlt.destinations.duckdb(str(duckdb_path)),
        dataset_name="bronze",
    )
    info = pipeline.run(source, write_disposition="replace")

    print("Data has been loaded successfully!")
    print(info)


if __name__ == "__main__":
    main()

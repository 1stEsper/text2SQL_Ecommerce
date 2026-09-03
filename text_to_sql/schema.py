import os
from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "ingestion" / "medallion.duckdb"

# Customer-level marts are intentionally excluded because they contain PII.
ALLOWED_RELATIONS = frozenset(
    {
        "dim_date",
        "dim_product",
        "dim_region",
        "fct_sales",
        "mart_product_performance",
        "mart_region_performance",
        "mart_sales_daily",
        "mart_sales_monthly",
    }
)


def get_database_path() -> Path:
    configured_path = os.getenv("T2S_DUCKDB_PATH")
    if not configured_path:
        return DEFAULT_DATABASE_PATH

    path = Path(configured_path).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def get_gold_schema() -> str:
    database_path = get_database_path()
    if not database_path.is_file():
        raise FileNotFoundError(f"DuckDB database not found: {database_path}")

    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        rows = connection.execute(
            """
            select table_name, column_name, data_type
            from information_schema.columns
            where table_schema = 'gold'
            order by table_name, ordinal_position
            """
        ).fetchall()
    finally:
        connection.close()

    tables: dict[str, list[str]] = {}
    for table_name, column_name, data_type in rows:
        if table_name in ALLOWED_RELATIONS:
            tables.setdefault(table_name, []).append(
                f"{column_name} {data_type}"
            )

    if not tables:
        raise RuntimeError(
            "No approved gold models were found. Run the dbt transformation "
            "project before using text-to-SQL."
        )

    return "\n".join(
        f"gold.{table_name}: {', '.join(columns)}"
        for table_name, columns in sorted(tables.items())
    )


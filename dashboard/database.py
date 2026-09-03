from collections.abc import Sequence
from typing import Any

import duckdb
import pandas as pd

from text_to_sql.schema import get_database_path


def query_dataframe(
    sql: str,
    parameters: Sequence[Any] | None = None,
) -> pd.DataFrame:
    """Run a query with a short-lived, read-only DuckDB connection."""
    connection = duckdb.connect(
        str(get_database_path()),
        read_only=True,
        config={"enable_external_access": False},
    )
    try:
        return connection.execute(sql, parameters or []).fetchdf()
    finally:
        connection.close()


from dataclasses import dataclass
from typing import Any

import duckdb

from text_to_sql.schema import get_database_path


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]


def execute_sql(sql: str) -> QueryResult:
    connection = duckdb.connect(
        str(get_database_path()),
        read_only=True,
        config={"enable_external_access": False},
    )
    try:
        cursor = connection.execute(sql)
        columns = tuple(column[0] for column in cursor.description)
        rows = tuple(cursor.fetchall())
        return QueryResult(columns=columns, rows=rows)
    finally:
        connection.close()


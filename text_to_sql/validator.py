import re

from sqlglot import exp, parse
from sqlglot.errors import ParseError

from text_to_sql.schema import ALLOWED_RELATIONS


DEFAULT_MAX_ROWS = 100

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(ALTER|ATTACH|CALL|COPY|CREATE|DELETE|DETACH|DROP|EXECUTE|EXPORT|"
    r"GRANT|IMPORT|INSERT|INSTALL|LOAD|MERGE|PRAGMA|REPLACE|REVOKE|SET|"
    r"TRUNCATE|UPDATE|USE|VACUUM)\b",
    flags=re.IGNORECASE,
)

FORBIDDEN_FUNCTIONS = frozenset(
    {
        "glob",
        "http_get",
        "http_post",
        "parquet_scan",
        "query",
        "query_table",
        "read_blob",
        "read_csv",
        "read_csv_auto",
        "read_json",
        "read_json_auto",
        "read_ndjson",
        "read_parquet",
        "read_text",
        "sqlite_scan",
    }
)

FORBIDDEN_NODE_TYPES = tuple(
    getattr(exp, name)
    for name in (
        "Alter",
        "Attach",
        "Command",
        "Copy",
        "Create",
        "Delete",
        "Detach",
        "Drop",
        "Grant",
        "Insert",
        "LoadData",
        "Merge",
        "Pragma",
        "Revoke",
        "Set",
        "Transaction",
        "TruncateTable",
        "Update",
        "Use",
    )
    if hasattr(exp, name)
)


def _function_name(function: exp.Func) -> str:
    if isinstance(function, exp.Anonymous):
        return function.name.lower()
    return function.sql_name().lower()


def validate_sql(sql: str, max_rows: int = DEFAULT_MAX_ROWS) -> str:
    if not sql.strip():
        raise ValueError("Gemini returned an empty SQL query")
    if max_rows < 1:
        raise ValueError("max_rows must be positive")
    if FORBIDDEN_KEYWORDS.search(sql):
        raise ValueError("The query contains a forbidden SQL operation")

    try:
        statements = parse(sql, read="duckdb")
    except ParseError as error:
        raise ValueError(f"Invalid DuckDB SQL: {error}") from error

    if len(statements) != 1:
        raise ValueError("Exactly one SQL statement is allowed")

    statement = statements[0]
    if not isinstance(statement, exp.Query):
        raise ValueError("Only SELECT queries are allowed")
    if isinstance(statement, FORBIDDEN_NODE_TYPES) or any(
        statement.find(node_type) is not None
        for node_type in FORBIDDEN_NODE_TYPES
    ):
        raise ValueError("Only read-only SELECT queries are allowed")

    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }
    referenced_gold_table = False

    for table in statement.find_all(exp.Table):
        table_name = table.name.lower()
        schema_name = table.db.lower() if table.db else ""

        if not schema_name and table_name in cte_names:
            continue
        if table.catalog:
            raise ValueError("Cross-database queries are not allowed")
        if schema_name != "gold":
            raise ValueError(
                f"Relation must be in the gold schema: {table.sql()}"
            )
        if table_name not in ALLOWED_RELATIONS:
            raise ValueError(f"Relation is not approved: gold.{table_name}")

        referenced_gold_table = True

    if not referenced_gold_table:
        raise ValueError("The query must reference an approved gold relation")

    for function in statement.find_all(exp.Func):
        function_name = _function_name(function)
        if function_name in FORBIDDEN_FUNCTIONS:
            raise ValueError(f"Function is not allowed: {function_name}")

    limit = statement.args.get("limit")
    if limit is None:
        statement = statement.limit(max_rows)
    else:
        limit_expression = limit.expression
        if not isinstance(limit_expression, exp.Literal) or not limit_expression.is_int:
            raise ValueError("LIMIT must be a fixed integer")
        if int(limit_expression.this) > max_rows:
            statement.set(
                "limit",
                exp.Limit(expression=exp.Literal.number(max_rows)),
            )

    return statement.sql(dialect="duckdb")


# Gemini text-to-SQL

This package converts natural-language analytics questions into DuckDB SQL.
Gemini only receives the approved gold schema; it never receives database
credentials or direct database access.

## Configuration

Add these values to the project `.env` file:

```dotenv
GEMINI_API_KEY=your-api-key
GEMINI_MODEL=gemini-3.6-flash
```

Build the dbt project before querying:

```bash
cd transformation
uv run dbt build --profiles-dir .
cd ..
```

Close any notebook or DuckDB CLI session that holds a conflicting database
lock, then run:

```bash
uv run python -m text_to_sql.cli "What was monthly revenue in 2023?"
```

The generated SQL is displayed and must be explicitly approved before it is
executed. Execution uses a read-only DuckDB connection with external access
disabled and returns at most 100 rows.


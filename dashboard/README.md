# E-commerce dashboard

The Streamlit dashboard reads the DuckDB gold layer without modifying it.

## Prerequisites

Build the dbt project and close other DuckDB sessions:

```bash
cd transformation
uv run dbt build --profiles-dir .
cd ..
```

To use the Ask Data page, configure `GEMINI_API_KEY` and `GEMINI_MODEL` in the
project `.env` file.

## Run

From the repository root:

```bash
uv run streamlit run dashboard/app.py
```

The main page provides filtered KPIs and deterministic charts. The Ask Data
page displays and validates Gemini-generated SQL and requires explicit approval
before executing it.


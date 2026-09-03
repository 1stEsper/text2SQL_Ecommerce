import os

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

from text_to_sql.schema import PROJECT_ROOT, get_gold_schema


DEFAULT_MODEL = "gemini-3.6-flash"


class GeneratedQuery(BaseModel):
    sql: str = Field(description="Exactly one read-only DuckDB SELECT query")
    explanation: str = Field(
        description="A short explanation of what the query calculates"
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Business or interpretation assumptions used by the query",
    )


def generate_sql(question: str) -> GeneratedQuery:
    if not question.strip():
        raise ValueError("The question cannot be empty")

    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to the project .env file."
        )

    schema = get_gold_schema()
    prompt = f"""
You translate business questions into DuckDB SQL.

AVAILABLE ANALYTICS SCHEMA
{schema}

RELATIONSHIPS
- gold.fct_sales.order_date = gold.dim_date.date_day
- gold.fct_sales.product_code = gold.dim_product.product_code
- gold.fct_sales.region_code = gold.dim_region.region_code

METRIC RULES
- Use SUM for revenue, profit, estimated_cost, and quantity.
- Recalculate aggregate profit margin as
  SUM(profit) / NULLIF(SUM(revenue), 0).
- Never sum discount or average row-level profit_margin.
- Use COUNT(DISTINCT order_id) for order counts.
- Use COUNT(DISTINCT customer_id) for customer counts.

SECURITY AND DIALECT RULES
- Generate exactly one DuckDB SELECT query.
- Only use the fully qualified relations listed above.
- Never use DDL, DML, PRAGMA, ATTACH, COPY, INSTALL, LOAD, or CALL.
- Never read files, URLs, environment variables, secrets, or system tables.
- Add LIMIT 100 to non-aggregate detail queries.
- Do not invent tables or columns.

USER QUESTION
{question.strip()}
"""

    client = genai.Client(api_key=api_key)
    try:
        interaction = client.interactions.create(
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": GeneratedQuery.model_json_schema(),
            },
        )
        return GeneratedQuery.model_validate_json(interaction.output_text)
    finally:
        client.close()


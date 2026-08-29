from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from text_to_sql.executor import execute_sql
from text_to_sql.generator import GeneratedQuery, generate_sql
from text_to_sql.validator import validate_sql


st.set_page_config(
    page_title="Ask Data",
    page_icon="✨",
    layout="wide",
)

st.title("Ask Data with Gemini")
st.caption(
    "Gemini generates SQL from approved gold models. Review the SQL before "
    "running it through the read-only DuckDB connection."
)

question = st.text_area(
    "Business question",
    placeholder="What was monthly revenue and profit in 2023?",
    height=100,
)

if st.button("Generate SQL", type="primary", disabled=not question.strip()):
    try:
        with st.spinner("Generating and validating SQL..."):
            generated = generate_sql(question)
            validated_sql = validate_sql(generated.sql)
        st.session_state["generated_query"] = generated.model_dump()
        st.session_state["validated_sql"] = validated_sql
        st.session_state.pop("query_result", None)
    except Exception as error:
        st.error(f"Could not generate SQL: {error}")

if "validated_sql" in st.session_state:
    generated = GeneratedQuery.model_validate(
        st.session_state["generated_query"]
    )
    sql = st.session_state["validated_sql"]

    st.subheader("Validated SQL")
    st.code(sql, language="sql")
    st.write(generated.explanation)

    if generated.assumptions:
        with st.expander("Assumptions"):
            for assumption in generated.assumptions:
                st.write(f"- {assumption}")

    st.warning("Execution is read-only, but review the SQL before approving it.")
    if st.button("Approve and execute", type="primary"):
        try:
            with st.spinner("Running query..."):
                result = execute_sql(sql)
            st.session_state["query_result"] = {
                "columns": result.columns,
                "rows": result.rows,
            }
        except Exception as error:
            st.error(f"Query failed: {error}")

if "query_result" in st.session_state:
    stored = st.session_state["query_result"]
    dataframe = pd.DataFrame(stored["rows"], columns=stored["columns"])

    st.subheader("Results")
    st.dataframe(dataframe, width="stretch", hide_index=True)

    numeric_columns = dataframe.select_dtypes(include="number").columns.tolist()
    all_columns = dataframe.columns.tolist()
    chart_type = st.selectbox("Visualization", ["Table", "Bar", "Line", "Scatter"])

    if chart_type != "Table" and all_columns and numeric_columns:
        x_column = st.selectbox("X axis", all_columns)
        y_column = st.selectbox("Y axis", numeric_columns)

        if chart_type == "Bar":
            figure = px.bar(dataframe, x=x_column, y=y_column)
        elif chart_type == "Line":
            figure = px.line(dataframe, x=x_column, y=y_column, markers=True)
        else:
            figure = px.scatter(dataframe, x=x_column, y=y_column)

        st.plotly_chart(figure, width="stretch")
    elif chart_type != "Table":
        st.info("The result needs at least one numeric column to draw a chart.")

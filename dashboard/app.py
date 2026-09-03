from datetime import date
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.queries import (
    EXCELLENT_MARGIN,
    GOOD_MARGIN,
    DashboardFilters,
    get_date_bounds,
    get_filter_options,
    load_discount_performance,
    load_kpis,
    load_monthly_performance,
    load_product_performance,
    load_region_performance,
    load_sale_quality,
)


st.set_page_config(
    page_title="E-commerce Analytics",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=60)
def cached_date_bounds() -> tuple[date, date]:
    return get_date_bounds()


@st.cache_data(ttl=60)
def cached_filter_options() -> dict[str, list[str]]:
    return get_filter_options()


@st.cache_data(ttl=60)
def load_dashboard(filters: DashboardFilters):
    return {
        "kpis": load_kpis(filters),
        "monthly": load_monthly_performance(filters),
        "quality": load_sale_quality(filters),
        "products": load_product_performance(filters),
        "regions": load_region_performance(filters),
        "discounts": load_discount_performance(filters),
    }


def optional_filter(value: str) -> str | None:
    return None if value == "All" else value


def money(value) -> str:
    if pd.isna(value):
        return "—"
    return f"${float(value):,.2f}"


st.title("E-commerce Analytics")
st.caption(
    "Read-only analytics from the DuckDB gold layer. "
    "Use the Ask Data page for Gemini-generated SQL."
)

try:
    minimum_date, maximum_date = cached_date_bounds()
    options = cached_filter_options()

    with st.sidebar:
        st.header("Filters")
        selected_dates = st.date_input(
            "Date range",
            value=(minimum_date, maximum_date),
            min_value=minimum_date,
            max_value=maximum_date,
        )
        category = st.selectbox(
            "Product category",
            ["All", *options["categories"]],
        )
        market = st.selectbox(
            "Market",
            ["All", *options["markets"]],
        )
        segment = st.selectbox(
            "Customer segment",
            ["All", *options["segments"]],
        )
        st.divider()
        st.caption(
            f"Good margin ≥ {GOOD_MARGIN:.2%}\n\n"
            f"Excellent margin ≥ {EXCELLENT_MARGIN:.0%}"
        )

    if not isinstance(selected_dates, (tuple, list)) or len(selected_dates) != 2:
        st.info("Select both a start date and an end date.")
        st.stop()

    filters = DashboardFilters(
        start_date=selected_dates[0],
        end_date=selected_dates[1],
        category=optional_filter(category),
        market=optional_filter(market),
        segment=optional_filter(segment),
    )
    data = load_dashboard(filters)
    kpis = data["kpis"].iloc[0]

    metric_columns = st.columns(6)
    metric_columns[0].metric("Revenue", money(kpis["revenue"]))
    metric_columns[1].metric("Profit", money(kpis["profit"]))
    metric_columns[2].metric(
        "Profit margin",
        "—" if pd.isna(kpis["margin"]) else f"{float(kpis['margin']):.2%}",
    )
    metric_columns[3].metric("Orders", f"{int(kpis['orders'] or 0):,}")
    metric_columns[4].metric("Customers", f"{int(kpis['customers'] or 0):,}")
    metric_columns[5].metric(
        "Profitable sales",
        "—"
        if pd.isna(kpis["profitable_sales_percentage"])
        else f"{float(kpis['profitable_sales_percentage']):.2f}%",
    )

    trend_tab, quality_tab, product_tab, region_tab = st.tabs(
        ["Trends", "Sale quality", "Products", "Regions"]
    )

    with trend_tab:
        monthly = data["monthly"]
        if monthly.empty:
            st.info("No sales match the selected filters.")
        else:
            trend = px.line(
                monthly,
                x="month",
                y=["revenue", "profit"],
                markers=True,
                title="Monthly revenue and profit",
                labels={"value": "Amount", "variable": "Metric"},
            )
            st.plotly_chart(trend, width="stretch")

            margin = px.line(
                monthly,
                x="month",
                y="margin",
                markers=True,
                title="Monthly profit margin",
            )
            margin.update_yaxes(tickformat=".1%")
            margin.add_hline(
                y=GOOD_MARGIN,
                line_dash="dash",
                annotation_text="Good-sale benchmark",
            )
            st.plotly_chart(margin, width="stretch")

    with quality_tab:
        quality = data["quality"]
        left, right = st.columns(2)
        color_map = {
            "Excellent": "#16a34a",
            "Good": "#65a30d",
            "Low margin": "#f59e0b",
            "Unprofitable": "#dc2626",
        }
        quality_chart = px.bar(
            quality,
            x="sale_quality",
            y="sales_count",
            color="sale_quality",
            color_discrete_map=color_map,
            title="Sales lines by quality",
        )
        left.plotly_chart(quality_chart, width="stretch")

        discount_chart = px.bar(
            data["discounts"],
            x="discount_band",
            y="profit",
            color="margin",
            color_continuous_scale="RdYlGn",
            title="Profit by discount band",
        )
        right.plotly_chart(discount_chart, width="stretch")
        st.dataframe(quality, width="stretch", hide_index=True)

    with product_tab:
        products = data["products"]
        product_chart = px.scatter(
            products,
            x="revenue",
            y="margin",
            size="units_sold",
            color="category",
            hover_name="product_name",
            title="Top products: revenue versus margin",
        )
        product_chart.update_yaxes(tickformat=".1%")
        product_chart.add_hline(y=GOOD_MARGIN, line_dash="dash")
        st.plotly_chart(product_chart, width="stretch")
        st.dataframe(products, width="stretch", hide_index=True)

    with region_tab:
        regions = data["regions"]
        region_chart = px.bar(
            regions.sort_values("revenue"),
            x="revenue",
            y="country",
            color="market",
            orientation="h",
            title="Top countries by revenue",
        )
        st.plotly_chart(region_chart, width="stretch")
        st.dataframe(regions, width="stretch", hide_index=True)

except Exception as error:
    st.error(f"Dashboard could not load: {error}")
    st.info(
        "Build the dbt models and close conflicting DuckDB sessions, then reload."
    )

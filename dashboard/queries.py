from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from dashboard.database import query_dataframe


GOOD_MARGIN = 0.1635
EXCELLENT_MARGIN = 0.40


@dataclass(frozen=True)
class DashboardFilters:
    start_date: date
    end_date: date
    category: str | None = None
    market: str | None = None
    segment: str | None = None


def get_date_bounds() -> tuple[date, date]:
    row = query_dataframe(
        """
        select min(order_date) as minimum_date,
               max(order_date) as maximum_date
        from gold.fct_sales
        """
    ).iloc[0]
    return row["minimum_date"], row["maximum_date"]


def get_filter_options() -> dict[str, list[str]]:
    categories = query_dataframe(
        """
        select distinct category
        from gold.dim_product
        where product_code <> 'UNKNOWN' and category is not null
        order by category
        """
    )["category"].tolist()
    markets = query_dataframe(
        """
        select distinct market
        from gold.dim_region
        where region_code <> 'UNKNOWN' and market is not null
        order by market
        """
    )["market"].tolist()
    segments = query_dataframe(
        """
        select distinct segment
        from gold.fct_sales
        where segment is not null
        order by segment
        """
    )["segment"].tolist()
    return {
        "categories": categories,
        "markets": markets,
        "segments": segments,
    }


def _filtered_sales(filters: DashboardFilters) -> tuple[str, list[Any]]:
    clauses = ["sales.order_date between ? and ?"]
    parameters: list[Any] = [filters.start_date, filters.end_date]

    if filters.category:
        clauses.append("product.category = ?")
        parameters.append(filters.category)
    if filters.market:
        clauses.append("region.market = ?")
        parameters.append(filters.market)
    if filters.segment:
        clauses.append("sales.segment = ?")
        parameters.append(filters.segment)

    sql = f"""
    with filtered_sales as (
        select
            sales.*,
            product.product_name,
            product.category,
            product.subcategory,
            region.city,
            region.country,
            region.region,
            region.market,
            region.country_latitude,
            region.country_longitude
        from gold.fct_sales as sales
        left join gold.dim_product as product
            on sales.product_code = product.product_code
        left join gold.dim_region as region
            on sales.region_code = region.region_code
        where {' and '.join(clauses)}
    )
    """
    return sql, parameters


def load_kpis(filters: DashboardFilters) -> pd.DataFrame:
    cte, parameters = _filtered_sales(filters)
    return query_dataframe(
        cte
        + """
        select
            round(sum(revenue), 2) as revenue,
            round(sum(profit), 2) as profit,
            round(sum(profit) / nullif(sum(revenue), 0), 4) as margin,
            count(distinct order_id) as orders,
            count(distinct customer_id) as customers,
            round(
                100.0 * count(*) filter (where profit > 0) / nullif(count(*), 0),
                2
            ) as profitable_sales_percentage
        from filtered_sales
        """,
        parameters,
    )


def load_monthly_performance(filters: DashboardFilters) -> pd.DataFrame:
    cte, parameters = _filtered_sales(filters)
    return query_dataframe(
        cte
        + """
        select
            cast(date_trunc('month', order_date) as date) as month,
            round(sum(revenue), 2) as revenue,
            round(sum(profit), 2) as profit,
            round(sum(profit) / nullif(sum(revenue), 0), 4) as margin
        from filtered_sales
        group by month
        order by month
        """,
        parameters,
    )


def load_sale_quality(filters: DashboardFilters) -> pd.DataFrame:
    cte, parameters = _filtered_sales(filters)
    return query_dataframe(
        cte
        + f"""
        select
            case
                when profit <= 0 then 'Unprofitable'
                when profit_margin >= {EXCELLENT_MARGIN} then 'Excellent'
                when profit_margin >= {GOOD_MARGIN} then 'Good'
                else 'Low margin'
            end as sale_quality,
            count(*) as sales_count,
            round(sum(revenue), 2) as revenue,
            round(sum(profit), 2) as profit
        from filtered_sales
        group by sale_quality
        order by sales_count desc
        """,
        parameters,
    )


def load_product_performance(filters: DashboardFilters) -> pd.DataFrame:
    cte, parameters = _filtered_sales(filters)
    return query_dataframe(
        cte
        + """
        select
            product_code,
            product_name,
            category,
            sum(quantity) as units_sold,
            round(sum(revenue), 2) as revenue,
            round(sum(profit), 2) as profit,
            round(sum(profit) / nullif(sum(revenue), 0), 4) as margin
        from filtered_sales
        group by product_code, product_name, category
        order by revenue desc
        limit 30
        """,
        parameters,
    )


def load_region_performance(filters: DashboardFilters) -> pd.DataFrame:
    cte, parameters = _filtered_sales(filters)
    return query_dataframe(
        cte
        + """
        select
            market,
            country,
            count(distinct order_id) as orders,
            round(sum(revenue), 2) as revenue,
            round(sum(profit), 2) as profit,
            round(sum(profit) / nullif(sum(revenue), 0), 4) as margin
        from filtered_sales
        group by market, country
        order by revenue desc
        limit 25
        """,
        parameters,
    )


def load_discount_performance(filters: DashboardFilters) -> pd.DataFrame:
    cte, parameters = _filtered_sales(filters)
    return query_dataframe(
        cte
        + """
        select
            case
                when discount = 0 then 'No discount'
                when discount <= 0.10 then '1-10%'
                when discount <= 0.20 then '11-20%'
                when discount <= 0.40 then '21-40%'
                else 'Over 40%'
            end as discount_band,
            case
                when discount = 0 then 1
                when discount <= 0.10 then 2
                when discount <= 0.20 then 3
                when discount <= 0.40 then 4
                else 5
            end as band_order,
            count(*) as sales_count,
            round(sum(revenue), 2) as revenue,
            round(sum(profit), 2) as profit,
            round(sum(profit) / nullif(sum(revenue), 0), 4) as margin
        from filtered_sales
        group by discount_band, band_order
        order by band_order
        """,
        parameters,
    )


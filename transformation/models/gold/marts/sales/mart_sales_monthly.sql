with monthly_sales as (

      select
          cast(date_trunc('month', order_date) as date) as month_start,

          count(*) as sales_line_count,
          count(distinct order_id) as order_count,
          count(distinct customer_id) as customer_count,

          sum(quantity) as units_sold,
          round(sum(revenue), 2) as revenue,
          round(sum(estimated_cost), 2) as estimated_cost,
          round(sum(profit), 2) as profit,

          round(
              sum(profit) / nullif(sum(revenue), 0),
              4
          ) as profit_margin,

          round(
              sum(discount * revenue) / nullif(sum(revenue), 0),
              4
          ) as weighted_average_discount

      from {{ ref('fct_sales') }}

      group by month_start

  ),

  with_previous_month as (

      select
          *,
          LAG(revenue) OVER (
            ORDER BY month_start
          ) AS previous_month_revenue, 
          LAG(profit) OVER (
            ORDER BY month_start
          ) AS previous_month_profit
      from monthly_sales

  )

  select
      month_start,
      extract(year from month_start)::integer as order_year,
      extract(month from month_start)::integer as order_month,

      sales_line_count,
      order_count,
      customer_count,
      units_sold,
      revenue,
      estimated_cost,
      profit,
      profit_margin,
      weighted_average_discount,

      round(
          (revenue - previous_month_revenue)
          / nullif(previous_month_revenue, 0),
          4
      ) as month_over_month_revenue_growth,

      round(
          (profit - previous_month_profit)
          / nullif(abs(previous_month_profit), 0),
          4
      ) as month_over_month_profit_growth

from with_previous_month

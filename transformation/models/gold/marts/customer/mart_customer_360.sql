select
    customer.customer_id,
    customer.first_name,
    customer.last_name,
    customer.full_name,
    customer.gender,
    customer.marital_status,
    customer.email_address,
    customer.annual_income,
    customer.education_level,
    customer.occupation,
    customer.is_home_owner,

    min(sales.order_date) as first_order_date,
    max(sales.order_date) as last_order_date,

    count(*) as sales_line_count,
    count(distinct sales.order_id) as order_count,
    count(distinct sales.product_code) as distinct_products_purchased,
    count(distinct sales.region_code) as distinct_regions,

    sum(sales.quantity) as lifetime_units,
    round(sum(sales.revenue), 2) as lifetime_revenue,
    round(sum(sales.estimated_cost), 2) as lifetime_estimated_cost,
    round(sum(sales.profit), 2) as lifetime_profit,

    round(
        sum(sales.profit) / nullif(sum(sales.revenue), 0),
        4
    ) as lifetime_profit_margin,

    round(
        sum(sales.revenue) / nullif(count(distinct sales.order_id), 0),
        2
    ) as average_order_value,

    round(
        sum(sales.revenue) / nullif(sum(sales.quantity), 0),
        2
    ) as average_revenue_per_unit

from {{ ref('fct_sales') }} as sales

inner join {{ ref('dim_customer') }} as customer
    on sales.customer_id = customer.customer_id

group by
    customer.customer_id,
    customer.first_name,
    customer.last_name,
    customer.full_name,
    customer.gender,
    customer.marital_status,
    customer.email_address,
    customer.annual_income,
    customer.education_level,
    customer.occupation,
    customer.is_home_owner

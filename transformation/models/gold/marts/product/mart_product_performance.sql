select
    product.product_code,
    product.product_name,
    product.category,
    product.subcategory,

    count(*) as sales_line_count,
    count(distinct sales.order_id) as order_count,
    count(distinct sales.customer_id) as customer_count,
    sum(sales.quantity) as units_sold,

    round(sum(sales.revenue), 2) as revenue,
    round(sum(sales.estimated_cost), 2) as estimated_cost,
    round(sum(sales.profit), 2) as profit,

    round(
        sum(sales.profit) / nullif(sum(sales.revenue), 0),
        4
    ) as profit_margin,

    round(
        sum(sales.revenue) / nullif(sum(sales.quantity), 0),
        2
    ) as average_revenue_per_unit,

    round(
        sum(sales.discount * sales.revenue) / nullif(sum(sales.revenue), 0),
        4
    ) as weighted_average_discount,

    min(sales.order_date) as first_sale_date,
    max(sales.order_date) as last_sale_date

from {{ ref('fct_sales') }} as sales

inner join {{ ref('dim_product') }} as product
    on sales.product_code = product.product_code

group by
    product.product_code,
    product.product_name,
    product.category,
    product.subcategory

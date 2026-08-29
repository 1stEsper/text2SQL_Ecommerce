with ranked as (
    select
        row_id,
        nullif(trim(order_id), '') as order_id,
        order_date,
        cast(date_trunc('month', order_date) as date) as order_month,
        extract(year from order_date)::integer as order_year,
        nullif(trim(customer_id), '') as customer_id,
        nullif(trim(segment), '') as segment,
        nullif(trim(region_code), '') as region_code,
        nullif(trim(product_code), '') as product_code,
        quantity,
        sales,
        discount,
        profit,
        round(sales - profit, 2) as estimated_cost,
        round(profit / nullif(sales, 0), 4) as profit_margin,
        _dlt_load_id as dlt_load_id,
        row_number() over (
            partition by row_id
            order by _dlt_load_id desc, _dlt_id desc
        ) as record_rank
    from {{ source('bronze', 'ecom_sales') }}
)

select * exclude (record_rank)
from ranked
where record_rank = 1

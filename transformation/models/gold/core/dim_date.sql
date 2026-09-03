with date_bounds as (
    select
        min(order_date) as minimum_date,
        max(order_date) as maximum_date
    from {{ ref('silver_sales') }}
),

date_spine as (
    select cast(date_value as date) as date_day
    from date_bounds,
    unnest(
        generate_series(
            minimum_date,
            maximum_date,
            interval '1 day'
        )
    ) as dates(date_value)
)

select
    date_day,
    extract(year from date_day)::integer as year,
    extract(quarter from date_day)::integer as quarter,
    extract(month from date_day)::integer as month_number,
    strftime(date_day, '%B') as month_name,
    extract(week from date_day)::integer as week_number,
    extract(day from date_day)::integer as day_of_month,
    strftime(date_day, '%A') as day_name,
    extract(dayofweek from date_day) in (0, 6) as is_weekend
from date_spine

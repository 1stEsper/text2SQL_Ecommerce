with ranked as (
    select
        nullif(trim(product_code), '') as product_code,
        nullif(trim(product), '') as product_name,
        nullif(trim(category), '') as category,
        nullif(trim(subcategory), '') as subcategory,
        _dlt_load_id as dlt_load_id,
        row_number() over (
            partition by product_code
            order by _dlt_load_id desc, _dlt_id desc
        ) as record_rank
    from {{ source('bronze', 'product') }}
)

select * exclude (record_rank)
from ranked
where record_rank = 1

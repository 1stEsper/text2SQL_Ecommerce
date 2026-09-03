with ranked as (
    select
        nullif(trim(region_code), '') as region_code,
        nullif(trim(city), '') as city,
        nullif(trim(state), '') as state,
        nullif(trim(country), '') as country,
        country_latitude,
        country_longitude,
        nullif(trim(region), '') as region,
        nullif(trim(market), '') as market,
        _dlt_load_id as dlt_load_id,
        row_number() over (
            partition by region_code
            order by _dlt_load_id desc, _dlt_id desc
        ) as record_rank
    from {{ source('bronze', 'region') }}
)

select * exclude (record_rank)
from ranked
where record_rank = 1

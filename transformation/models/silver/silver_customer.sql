with ranked as (
    select
        nullif(trim(customer_id), '') as customer_id,
        nullif(trim(first_name), '') as first_name,
        nullif(trim(last_name), '') as last_name,
        birth_date,
        case upper(trim(marital_status))
            when 'M' then 'Married'
            when 'S' then 'Single'
        end as marital_status,
        case upper(trim(gender))
            when 'M' then 'Male'
            when 'F' then 'Female'
        end as gender,
        lower(nullif(trim(email_address), '')) as email_address,
        annual_income,
        nullif(trim(education_level), '') as education_level,
        nullif(trim(occupation), '') as occupation,
        case upper(trim(home_owner))
            when 'Y' then true
            when 'N' then false
        end as is_home_owner,
        _dlt_load_id as dlt_load_id,
        row_number() over (
            partition by customer_id
            order by _dlt_load_id desc, _dlt_id desc
        ) as record_rank
    from {{ source('bronze', 'customer') }}
)

select * exclude (record_rank)
from ranked
where record_rank = 1

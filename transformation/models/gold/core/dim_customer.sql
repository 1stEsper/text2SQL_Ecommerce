SELECT
    customer_id, 
    first_name, 
    last_name, 
    first_name || ' ' || last_name AS full_name, 
    birth_date, 
    marital_status, 
    gender, 
    email_address, 
    annual_income, 
    education_level, 
    occupation, 
    is_home_owner
FROM {{ ref('silver_customer') }}

UNION ALL 

SELECT
    'UNKNOWN',
    'Unknown',
    'Unknown',
    'Unknown',
    null,
    null,
    null,
    null,
    null,
    null,
    null,
    null

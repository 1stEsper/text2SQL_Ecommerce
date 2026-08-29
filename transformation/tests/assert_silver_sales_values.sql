SELECT * FROM {{ ref('silver_sales') }}
WHERE quantity <= 0 OR sales < 0 OR discount < 0 OR discount >1 
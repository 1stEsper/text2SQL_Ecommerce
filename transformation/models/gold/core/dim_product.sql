SELECT
      product_code,
      product_name,
      category,
      subcategory
FROM {{ ref('silver_product') }}

UNION ALL

SELECT
      'UNKNOWN',
      'Unknown product',
      'Unknown',
      'Unknown'

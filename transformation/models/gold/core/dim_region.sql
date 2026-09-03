SELECT
      region_code,
      city,
      state,
      country,
      country_latitude,
      country_longitude,
      region,
      market
FROM {{ ref('silver_region') }}

UNION ALL

SELECT
      'UNKNOWN',
      'Unknown',
      'Unknown',
      'Unknown',
      null,
      null,
      'Unknown',
      'Unknown'

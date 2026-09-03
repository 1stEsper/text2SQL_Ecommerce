SELECT 
    order_date, 
    EXTRACT(year FROM order_date)::integer AS year, 
    EXTRACT(month FROM order_date)::integer AS month, 
    EXTRACT(dayofweek FROM order_date)::integer AS day_of_week,
    COUNT(*) AS sales_line_count,  
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT customer_id) AS customer_count, 
    SUM(quantity) AS units_sold, 
    ROUND(SUM(revenue), 2) AS revenue, 
    ROUND(SUM(estimated_cost), 2) AS estimated_cost,
    ROUND(SUM(profit), 2) AS profit, 
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0), 4) AS profit_margin, 
    ROUND(
        SUM(discount * revenue) / NULLIF(SUM(revenue), 0), 4
    ) AS weighted_average_discount, 
    COUNT(*) FILTER(WHERE profit < 0) AS unprofitable_line_count

FROM {{ ref('fct_sales') }}
GROUP BY order_date

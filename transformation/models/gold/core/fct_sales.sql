SELECT
      sales.row_id,
      sales.order_id,
      sales.order_date,
      sales.customer_id,

      case
          when product.product_code is null then 'UNKNOWN'
          else sales.product_code
      end as product_code,

      case
          when region.region_code is null then 'UNKNOWN'
          else sales.region_code
      end as region_code,

      sales.segment,
      sales.quantity,
      sales.sales as revenue,
      sales.discount,
      sales.profit,
      sales.estimated_cost,
      sales.profit_margin
  from {{ ref('silver_sales') }} as sales

  left join {{ ref('silver_product') }} as product
      on sales.product_code = product.product_code

  left join {{ ref('silver_region') }} as region
      on sales.region_code = region.region_code

{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT customer_segment_type,
       language_type,
       sum(case when conversion_rate > 0.08 then 1 else 0 end) as high_conversion_campaigns,
       sum(case when conversion_rate <= 0.08 then 1 else 0 end) as low_conversion_campaigns
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 1, 2
ORDER BY 3 DESC, 4 DESC

{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT channel_type,
       audience_type,
       sum(case when impressions > 5500 then 1 else 0 end) as campaigns_with_impressions,
       sum(case when impressions = 0 then 1 else 0 end) as campaigns_without_impressions
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 1, 2
ORDER BY 3 DESC, 4 DESC

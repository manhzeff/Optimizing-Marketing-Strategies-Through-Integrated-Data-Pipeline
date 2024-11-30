{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT campaign_type_name,
       company_name,
       sum(case when roi > 0 then 1 else 0 end) as positive_roi_campaigns,
       sum(case when roi <= 0 then 1 else 0 end) as negative_roi_campaigns
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 1, 2
ORDER BY 3 DESC, 4 DESC

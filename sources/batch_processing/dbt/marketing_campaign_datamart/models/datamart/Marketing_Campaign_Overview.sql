{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT campaign_type_name,
       company_name,
       audience_type,
       sum(case when clicks > 0 then 1 else 0 end) as successful_campaigns,
       sum(case when clicks = 0 then 1 else 0 end) as unsuccessful_campaigns
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 1, 2, 3
ORDER BY 4 DESC, 5 DESC

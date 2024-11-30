{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT 
    company_name,
    location,  -- Thêm yếu tố location vào SELECT
    sum(case when roi > 5 then 1 else 0 end) as positive_roi_campaigns,
    sum(case when roi <= 5 then 1 else 0 end) as negative_roi_campaigns
FROM {{ ref('stg_fact_marketing') }}
GROUP BY company_name, location  -- Thêm location vào GROUP BY
ORDER BY positive_roi_campaigns DESC, negative_roi_campaigns DESC

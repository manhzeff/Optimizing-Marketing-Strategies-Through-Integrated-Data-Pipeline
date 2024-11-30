{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT 
    company_name,
    audience_type,
    -- Tổng chiến dịch thành công (clicks > 200)
    sum(case when clicks > 500 then 1 else 0 end) as successful_campaigns,
    
    -- Tổng chiến dịch không thành công (clicks = 0)
    sum(case when clicks < 260 then 1 else 0 end) as unsuccessful_campaigns,
    
    -- Tổng chiến dịch có clicks từ 1 đến 200
    sum(case when clicks > 260 and clicks <= 500 then 1 else 0 end) as medium_successful_campaigns
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 1, 2
ORDER BY successful_campaigns DESC, unsuccessful_campaigns DESC, medium_successful_campaigns DESC

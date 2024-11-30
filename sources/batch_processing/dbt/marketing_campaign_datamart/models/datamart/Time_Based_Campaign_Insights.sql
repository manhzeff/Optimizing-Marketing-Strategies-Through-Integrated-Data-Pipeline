{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT campaign_id,
       Date,
       -- Tính chiến dịch có tương tác cao và thấp bằng cách sử dụng FILTER để tối ưu hiệu suất
       SUM(CASE WHEN engagement_score > 50 THEN 1 ELSE 0 END) AS high_engagement_campaigns,
       SUM(CASE WHEN engagement_score <= 50 THEN 1 ELSE 0 END) AS low_engagement_campaigns
FROM {{ ref('Time_Partitioned_Campaign_Performance') }}
GROUP BY campaign_id, Date
ORDER BY high_engagement_campaigns DESC, low_engagement_campaigns DESC

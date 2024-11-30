{{ 
  config(
    materialized = 'view'
  ) 
}}

SELECT 
    campaign_id,
    Date,
    SUM(CASE WHEN engagement_score > 5 THEN 1 ELSE 0 END) AS high_engagement_campaigns,
    SUM(CASE WHEN engagement_score <= 5 THEN 1 ELSE 0 END) AS low_engagement_campaigns
FROM {{ ref('Time_Partitioned_Campaign_Performance') }}
GROUP BY campaign_id, Date
ORDER BY high_engagement_campaigns DESC, low_engagement_campaigns DESC

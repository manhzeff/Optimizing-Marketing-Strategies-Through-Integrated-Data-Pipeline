
{{ config(materialized = 'view') }}

SELECT 
    DATE_TRUNC('month', Date) AS month_date,
    channel_type,
    COUNT(DISTINCT campaign_id) AS total_campaigns,
    AVG(Conversion_Rate) AS avg_conversion_rate,
    AVG(Engagement_Score) AS avg_engagement_score,
    AVG(ROI) AS avg_roi,
    SUM(Clicks) AS total_clicks,
    SUM(Impressions) AS total_impressions
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 
    DATE_TRUNC('month', Date),
    channel_type
ORDER BY 
    month_date ASC


{{ config(materialized = 'view') }}

SELECT 
    DATE_TRUNC('month', Date) AS month_date,
    location,
    language_type,
    COUNT(DISTINCT campaign_id) AS total_campaigns,
    AVG(ROI) AS avg_roi,
    AVG(Conversion_Rate) AS avg_conversion_rate,
    SUM(Impressions) AS total_impressions,
    SUM(Clicks) AS total_clicks
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 
    DATE_TRUNC('month', Date),
    location,
    language_type
ORDER BY 
    month_date ASC

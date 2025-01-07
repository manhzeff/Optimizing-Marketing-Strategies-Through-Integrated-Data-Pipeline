
{{ config(materialized = 'view') }}

SELECT 
    DATE_TRUNC('month', Date) AS month_date,
    customer_segment_type,
    COUNT(DISTINCT campaign_id) AS total_campaigns,
    AVG(ROI) AS avg_roi,
    AVG(Acquisition_Cost) AS avg_acquisition_cost,
    SUM(Clicks) AS total_clicks
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 
    DATE_TRUNC('month', Date),
    customer_segment_type
ORDER BY 
    month_date ASC

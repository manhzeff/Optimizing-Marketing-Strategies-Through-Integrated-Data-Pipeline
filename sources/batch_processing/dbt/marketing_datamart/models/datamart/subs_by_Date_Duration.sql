-- models/marts/subs_by_date_duration.sql

{{ config(materialized = 'view') }}

SELECT
    DATE_TRUNC('month', Date) AS month_date,
    CASE 
        WHEN duration = 15 THEN 'Short'
        WHEN duration = 30 THEN 'Medium'
        WHEN duration = 45 THEN 'Long'
        WHEN duration = 60 THEN 'Extra-long'
        ELSE 'Undefined'
    END AS duration_bucket,
    COUNT(DISTINCT campaign_id) AS total_campaigns,
    AVG(Conversion_Rate) AS avg_conversion_rate,
    SUM(Clicks) AS total_clicks
FROM {{ ref('stg_fact_marketing') }}
GROUP BY 
    DATE_TRUNC('month', Date),
    CASE 
        WHEN duration = 15 THEN 'Short'
        WHEN duration = 30 THEN 'Medium'
        WHEN duration = 45 THEN 'Long'
        WHEN duration = 60 THEN 'Extra-long'
        ELSE 'Undefined'
    END
ORDER BY month_date ASC


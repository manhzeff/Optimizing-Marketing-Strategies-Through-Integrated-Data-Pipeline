{{
  config(
    materialized = 'view',
  )
}}

SELECT 
    campaign_id,
    -- campaign_type_name,
    company_name,
    audience_type,
    duration,
    channel_type,
    Conversion_Rate,
    Acquisition_Cost,
    ROI,
    language_type,
    Clicks,
    location,
    Impressions,
    Engagement_Score,
    customer_segment_type,
    Date
FROM 
    {{ source('COMPUTE_WH','fact_marketing')}} as fact 
    -- LEFT JOIN {{ source('COMPUTE_WH','dim_campaign') }} as ct ON fact.campaign_type_id = ct.campaign_type_id
    LEFT JOIN {{ source('COMPUTE_WH','dim_channel')}} as ch ON fact.channel_id = ch.channel_id
    LEFT JOIN {{ source('COMPUTE_WH','dim_company') }} as co ON fact.company_id = co.company_id
    LEFT JOIN {{ source('COMPUTE_WH','dim_target_audience') }} as ta ON fact.audience_id = ta.audience_id
    LEFT JOIN {{ source('COMPUTE_WH','dim_customer_segment') }} as cs ON fact.customer_segment_id = cs.customer_segment_id
    LEFT JOIN {{ source('COMPUTE_WH','dim_language') }} as la ON fact.language_id = la.language_id
ORDER BY 1

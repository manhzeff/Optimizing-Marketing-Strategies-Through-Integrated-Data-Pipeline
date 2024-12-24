{{
  config(
    materialized = 'table',
    unique_key = 'campaign_id'
  )
}}

SELECT 
    campaign_id,
    campaign_type_id
    company_id,
    audience_id,
    duration,
    channel_id,
    Conversion_Rate,
    Acquisition_Cost,
    ROI,
    location,
    language_id,
    Clicks,
    Impressions,
    Engagement_Score,
    customer_segment_id,
    Date
FROM
    {{ ref('stg_marketing') }} as stg
    LEFT JOIN {{ ref('dim_campaign') }} as ct ON stg.campaign_type = ct.campaign_type_name
    LEFT JOIN {{ ref('dim_channel') }} as ch ON stg.Channel_Used = ch.channel_type
    LEFT JOIN {{ ref('dim_company') }} as co ON stg.Company = co.company_name
    LEFT JOIN {{ ref('dim_target_audience') }} as ta ON stg.Target_Audience = ta.audience_type
    LEFT JOIN {{ ref('dim_customer_segment') }} as cs ON stg.Customer_Segment = cs.customer_segment_type
    LEFT JOIN {{ ref('dim_language') }} as la ON stg.Language = la.language_type
ORDER BY 1

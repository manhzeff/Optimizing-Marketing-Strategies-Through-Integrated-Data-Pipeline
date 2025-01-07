{{
  config(
    materialized = 'table',
    unique_key = 'campaign_type_id'
  )
}}

select distinct
    {{ encode_campaign('Campaign_Type') }} as campaign_type_id,
    Campaign_Type as campaign_type_name
from {{ ref('stg_marketing') }}
order by campaign_type_id asc

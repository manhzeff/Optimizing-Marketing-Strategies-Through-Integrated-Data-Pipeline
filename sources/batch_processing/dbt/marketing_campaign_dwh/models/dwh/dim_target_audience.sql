{{
  config(
    materialized = 'table',
    unique_key = 'audience_id'
  )
}}

select distinct
    {{ encode_target_audience('Target_Audience') }} as audience_id,
    Target_Audience as audience_type
from {{ ref('stg_marketing') }}
order by audience_id asc

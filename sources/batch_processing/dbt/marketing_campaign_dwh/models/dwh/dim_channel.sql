{{
  config(
    materialized = 'table',
    unique_key = 'channel_id'
  )
}}

select distinct
    {{ encode_channel('Channel_Used') }} as channel_id,
    Channel_Used as channel_type
from {{ ref('stg_marketing') }}
order by channel_id asc

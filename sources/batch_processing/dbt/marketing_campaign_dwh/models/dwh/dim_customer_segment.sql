{{
  config(
    materialized = 'table',
    unique_key = 'customer_segment_id'
  )
}}

select distinct
    {{ encode_customer_segment('Customer_Segment') }} as customer_segment_id,
    Customer_Segment as customer_segment_type
from {{ ref('stg_marketing') }}
order by customer_segment_id asc

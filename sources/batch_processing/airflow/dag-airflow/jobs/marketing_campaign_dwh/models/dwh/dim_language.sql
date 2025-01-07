{{
  config(
    materialized = 'table',
    unique_key = 'language_id'
  )
}}

select distinct
    {{ encode_language('Language') }} as language_id,
    Language as language_type
from {{ ref('stg_marketing') }}
order by language_id asc

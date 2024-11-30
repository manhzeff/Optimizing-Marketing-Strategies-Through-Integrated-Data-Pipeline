{{
  config(
    materialized = 'table',
    unique_key = 'company_id'
  )
}}

select distinct
    {{ encode_company('Company') }} as company_id,
    Company as company_name
from {{ ref('stg_marketing') }}
order by company_id asc

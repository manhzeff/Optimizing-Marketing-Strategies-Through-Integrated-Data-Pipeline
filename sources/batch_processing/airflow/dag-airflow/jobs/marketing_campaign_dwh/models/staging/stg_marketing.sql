{{ config(materialized='ephemeral') }}

SELECT *
FROM {{ source('COMPUTE_WH','MARKETING_SPARK')}}
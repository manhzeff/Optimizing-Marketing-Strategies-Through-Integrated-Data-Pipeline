{{ config(
    materialized = 'view',
    partition_by = {
        "field": "Date",
        "data_type": "timestamp",
        "granularity": "month"
    }
) }}

SELECT *
FROM {{ ref('stg_fact_marketing') }}  -- Tham chiếu bảng staging của bạn

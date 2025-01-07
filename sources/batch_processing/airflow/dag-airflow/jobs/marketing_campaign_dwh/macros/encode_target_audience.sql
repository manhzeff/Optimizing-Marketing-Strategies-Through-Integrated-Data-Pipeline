{# This macro encodes the Target_Audience column to numeric #}

{% macro encode_target_audience(column_name) -%}

    case {{ column_name }}
        when 'Men 18-24' then 1
        when 'Women 35-44' then 2
        when 'Men 25-34' then 3
        when 'All Ages' then 4
        when 'Women 25-34' then 5
    end

{%- endmacro %}

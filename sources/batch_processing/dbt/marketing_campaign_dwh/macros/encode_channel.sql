{# This macro encodes the Channel_Used column to numeric #}

{% macro encode_channel(column_name) -%}

    case {{ column_name }}
        when 'Google Ads' then 1
        when 'YouTube' then 2
        when 'Facebook' then 3
        when 'Instagram' then 4
        when 'Email' then 5
        when 'Website' then 6
    end

{%- endmacro %}

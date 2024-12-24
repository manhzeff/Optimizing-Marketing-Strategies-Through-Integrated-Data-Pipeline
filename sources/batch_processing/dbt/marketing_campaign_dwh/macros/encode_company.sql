{# This macro encodes the Company column to numeric #}

{% macro encode_company(column_name) -%}

    case {{ column_name }}
        when 'Innovate Industries' then 1
        when 'NexGen Systems' then 2
        when 'Alpha Innovations' then 3
        when 'DataTech Solutions' then 4
        when 'TechCorp'             then 5
    end

{%- endmacro %}

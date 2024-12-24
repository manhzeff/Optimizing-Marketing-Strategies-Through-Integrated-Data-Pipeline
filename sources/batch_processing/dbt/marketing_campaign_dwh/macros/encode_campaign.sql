{# This macro encodes the Campaign_Type column to numeric #}

{% macro encode_campaign(column_name) -%}

    case {{ column_name }}
        when 'Email' then 1
        when 'Influencer' then 2
        when 'Display' then 3
        when 'Social Media' then 4
        when 'Search' then 5
    end

{%- endmacro %}

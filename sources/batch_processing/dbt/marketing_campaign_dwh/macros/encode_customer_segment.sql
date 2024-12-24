{# This macro encodes the Customer_Segment column to numeric #}

{% macro encode_customer_segment(column_name) -%}

    case {{ column_name }}
        when 'Health & Wellness' then 1
        when 'Fashionistas' then 2
        when 'Outdoor Adventurers' then 3
        when 'Foodies' then 4
        when 'Tech Enthusiasts' then 5
    end

{%- endmacro %}

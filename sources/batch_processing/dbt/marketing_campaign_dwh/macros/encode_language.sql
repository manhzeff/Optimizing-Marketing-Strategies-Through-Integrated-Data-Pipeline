{# This macro encodes the Language column to numeric #}

{% macro encode_language(column_name) -%}

    case {{ column_name }}
        when 'Spanish' then 1
        when 'German' then 2
        when 'French' then 3
        when 'Mandarin' then 4
        when 'English' then 5
    end

{%- endmacro %}


#!/usr/bin/env bash

# Nâng cấp cơ sở dữ liệu Airflow
airflow db upgrade

# Tạo người dùng admin bằng các biến môi trường (hoặc giá trị mặc định nếu không có)
airflow users create \
    -r Admin \
    -u "${_AIRFLOW_WWW_USER_USERNAME:-admin}" \
    -p "${_AIRFLOW_WWW_USER_PASSWORD:-admin}" \
    -e "${_AIRFLOW_WWW_USER_EMAIL:-admin@example.com}" \
    -f "${_AIRFLOW_WWW_USER_FIRSTNAME:-admin}" \
    -l "${_AIRFLOW_WWW_USER_LASTNAME:-airflow}"

# Khởi động webserver của Airflow
exec airflow webserver

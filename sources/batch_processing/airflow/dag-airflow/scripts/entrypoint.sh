
#!/usr/bin/env bash

# Nâng cấp cơ sở dữ liệu Airflow
airflow db upgrade

# Tạo người dùng admin bằng các biến môi trường (hoặc giá trị mặc định nếu không có)
airflow users create -r Admin -u admin -p admin -e admin@example.com -f admin -l airflow


# Khởi động webserver của Airflow
airflow webserver

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pyspark_clean.py

File PySpark để đọc dữ liệu Parquet từ S3, làm sạch & transform, 
sau đó ghi vào bảng Snowflake.
"""

import os
from dotenv import load_dotenv


from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, regexp_replace, to_date, trim, upper, lower,
    when, expr, count, sum, lit
)
import pyspark.sql.functions as F

# ------------------------------------------------
# 1. Nạp biến môi trường (nếu dùng .env)
# ------------------------------------------------
load_dotenv()  # Thay "config" bằng tên file .env của bạn

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

if not aws_access_key_id or not aws_secret_access_key:
    raise ValueError("AWS credentials not found in environment variables.")

# ------------------------------------------------
# 2. Khởi tạo SparkSession với cấu hình đọc S3
# ------------------------------------------------

import os

# Tạo danh sách file .jar
jar_files = [
    "aws-java-sdk-bundle-1.11.1026.jar",
    "hadoop-aws-3.3.2.jar",
    "snowflake-jdbc-3.19.0.jar",
    "spark-snowflake_2.12-2.12.0-spark_3.4 (2).jar"
]
jar_dir = r"C:\Users\phamd\Desktop\New folder\Optimizing-Marketing-Strategies-Through-Integrated-Data-Pipeline\sources\batch_processing\sparkclean\lib"
jar_path = ",".join([os.path.join(jar_dir, jar) for jar in jar_files])


spark = SparkSession.builder \
    .appName("Read Parquet from S3") \
    .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id) \
    .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key) \
    .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.jars", jar_path)\
    .getOrCreate()

# ------------------------------------------------
# 3. Đọc file Parquet từ S3
# ------------------------------------------------
s3_file_path = "s3a://zeffmarketingbucket/raw/marketing_campaign_dataset.parquet"
df = spark.read.parquet(s3_file_path)

print("=== SHOW 5 ROWS ===")
df.show(5, truncate=False)

print("=== PRINT SCHEMA ===")
df.printSchema()

# ------------------------------------------------
# 4. Làm sạch dữ liệu
# ------------------------------------------------

# Ví dụ: làm sạch cột 'Acquisition_Cost' (bỏ ký tự $, dấu phẩy, rồi chuyển sang float)
df = df.withColumn(
    "Acquisition_Cost",
    regexp_replace(col("Acquisition_Cost"), r"[\$,]", "").cast("float")
)

# Đổi cột 'Date' sang kiểu ngày với định dạng 'yyyy-MM-dd'
df = df.withColumn("Date", to_date(col("Date"), "yyyy-MM-dd"))

# Bỏ chữ ' days' trong cột 'Duration', chuyển sang int
df = df.withColumn("Duration", regexp_replace(col("Duration"), " days", "").cast("int"))

# Kiểm tra và xử lý giá trị null
missing_values = df.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns])
print("=== MISSING VALUES BEFORE CLEANING ===")
missing_values.show()

# Lọc bỏ những hàng có giá trị âm ở một số cột numeric
numeric_columns = ["Conversion_Rate", "ROI", "Clicks", "Impressions", "Engagement_Score"]
for c_name in numeric_columns:
    df = df.filter(col(c_name) >= 0)

print("=== SAMPLE AFTER CLEANING ===")
df.show(10)

# ------------------------------------------------
# 5. Kiểm tra các giá trị distinct trong một số cột
# ------------------------------------------------
for col_name in ["Company", "Campaign_Type", "Target_Audience", 
                 "Channel_Used", "Language", "Customer_Segment"]:
    unique_vals = df.select(col_name).distinct().rdd.flatMap(lambda x: x).collect()
    print(f"Unique values in {col_name}:", unique_vals)

# ------------------------------------------------
# 6. Tạo bảng Snowflake (nếu chưa tồn tại) và ghi dữ liệu
# ------------------------------------------------
load_dotenv()  # Thay "config.env" bằng tên file .env của bạn

sf_options = {
    "sfURL": os.environ.get("SNOWFLAKE_URL"),
    "sfDatabase": os.environ.get("SNOWFLAKE_DB"),
    "sfSchema": os.environ.get("SNOWFLAKE_SCHEMA"),
    "sfWarehouse": os.environ.get("SNOWFLAKE_WAREHOUSE"),
    "sfUser": os.environ.get("SNOWFLAKE_USER"),
    "sfPassword": os.environ.get("SNOWFLAKE_PASSWORD")
}

# Tạo bảng marketing_spark trên Snowflake nếu chưa tồn tại
create_table_query = """
CREATE OR REPLACE TABLE marketing_spark (
    Campaign_ID STRING,
    Company STRING,
    Campaign_Type STRING,
    Target_Audience STRING,
    Duration STRING,
    Channel_Used STRING,
    Conversion_Rate FLOAT,
    Acquisition_Cost FLOAT,
    ROI FLOAT,
    Location STRING,
    Language STRING,
    Clicks INT,
    Impressions INT,
    Engagement_Score FLOAT,
    Customer_Segment STRING,
    Date DATE
)
"""

# Kết nối Snowflake để chạy lệnh CREATE TABLE
try:
    import snowflake.connector
    conn = snowflake.connector.connect(
        user=sf_options["sfUser"],
        password=sf_options["sfPassword"],
        account=sf_options["sfURL"].split(".snowflakecomputing.com")[0]
    )
    cur = conn.cursor()
    cur.execute(f"USE DATABASE {sf_options['sfDatabase']}")
    cur.execute(f"USE SCHEMA {sf_options['sfSchema']}")
    cur.execute(create_table_query)
    conn.close()
    print("Table marketing_spark created or replaced successfully in Snowflake!")
except Exception as e:
    print("Error creating table in Snowflake:", e)
    raise e

# Ghi DataFrame vào Snowflake
try:
    df.write \
      .format("snowflake") \
      .options(**sf_options) \
      .option("dbtable", "marketing_spark") \
      .mode("append") \
      .save()
    print("Data loaded to Snowflake successfully!")
except Exception as e:
    print("Error loading data to Snowflake:", e)
    raise e

# Kết thúc SparkSession
spark.stop()

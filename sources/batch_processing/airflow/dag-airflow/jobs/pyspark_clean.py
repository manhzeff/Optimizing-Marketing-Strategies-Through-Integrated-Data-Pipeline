import os
import sys
from snowflake.connector import connect
from snowflake.connector.pandas_tools import write_pandas
import pyspark.sql.functions as F

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, regexp_replace, to_date, trim, upper, lower, when, expr, count, sum, lit
)

# ------------------------------------
# 1. Định nghĩa các hàm xử lý
# ------------------------------------
def get_aws_credentials():
    """
    Lấy AWS Credentials từ biến môi trường (nếu chạy cục bộ).
    Trả về tuple (aws_access_key_id, aws_secret_access_key).
    """
    aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

    # Kiểm tra nếu cần
    if not aws_access_key_id or not aws_secret_access_key:
        print("WARNING: AWS credentials not found in environment variables.")
        print("If running on EMR Serverless or IAM-based environment, it may be fine.")
        # raise ValueError("AWS credentials not found.")

    return aws_access_key_id, aws_secret_access_key


def create_spark_session(aws_access_key_id, aws_secret_access_key, app_name="Read Parquet from S3"):
    """
    Khởi tạo SparkSession, tùy chọn cấu hình cho S3, Snowflake, etc.
    Trả về spark session.
    """
    spark_builder = SparkSession.builder.appName(app_name)

    # Ví dụ: đặt executor memory
    spark_builder = spark_builder.config("spark.executor.memory", "2g")

    # Nếu chạy cục bộ và cần credentials tĩnh
    # Trên EMR Serverless, thường không cần key/secret trong config
    spark_builder = (
        spark_builder
        .config("spark.hadoop.fs.s3a.access.key", aws_access_key_id)
        .config("spark.hadoop.fs.s3a.secret.key", aws_secret_access_key)
        .config("spark.hadoop.fs.s3a.endpoint", "s3.ap-southeast-2.amazonaws.com")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    )

    spark = spark_builder.getOrCreate()
    return spark


def read_parquet_from_s3(spark, s3_path):
    """
    Đọc file Parquet từ S3, trả về DataFrame spark.
    """
    print(f"=== Reading Parquet from {s3_path} ===")
    df = spark.read.parquet(s3_path)
    return df


def clean_data(df):
    """
    Thực hiện các bước làm sạch & kiểm tra dữ liệu:
    - Xử lý cột Acquisition_Cost (bỏ ký tự $, dấu phẩy, rồi float)
    - Chuyển cột Date sang kiểu DATE
    - Bỏ chữ " days" trong Duration -> int
    - Lọc bỏ hàng có giá trị âm ở các cột numeric
    - In missing values
    - Trả về DataFrame đã làm sạch
    """
    # Ví dụ: làm sạch cột 'Acquisition_Cost'
    df = df.withColumn(
        "Acquisition_Cost",
        regexp_replace(col("Acquisition_Cost"), r"[\$,]", "").cast("float")
    )

    # Đổi cột 'Date' sang kiểu ngày
    df = df.withColumn("Date", to_date(col("Date"), "yyyy-MM-dd"))

    # Bỏ ' days' trong cột 'Duration'
    df = df.withColumn("Duration", regexp_replace(col("Duration"), " days", "").cast("int"))

    # In missing values     
    missing_values = df.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns])
    missing_values.show()

    # Lọc bỏ hàng có giá trị âm
    numeric_columns = ["Conversion_Rate", "ROI", "Clicks", "Impressions", "Engagement_Score"]
    for c_name in numeric_columns:
        df = df.filter(col(c_name) >= 0)

    return df


def create_snowflake_table(sf_options, create_table_query):
    """
    Kết nối Snowflake, tạo table (nếu chưa tồn tại).
    """
    try:
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


def write_to_snowflake(df, sf_options, table_name="marketing_spark"):
    """
    Ghi DataFrame vào Snowflake, mode append.
    """
    try:
        df.write \
          .format("snowflake") \
          .options(**sf_options) \
          .option("dbtable", table_name) \
          .mode("append") \
          .save()
        print("Data loaded to Snowflake successfully!")
    except Exception as e:
        print("Error loading data to Snowflake:", e)
        raise e


def main():
    """
    Hàm main sẽ:
    1. Lấy AWS Credentials
    2. Tạo Spark Session
    3. Đọc file Parquet từ S3
    4. Làm sạch dữ liệu
    6. Tạo bảng Snowflake & ghi dữ liệu
    """
    # 1. Lấy AWS Credentials (nếu cần cục bộ)
    aws_access_key_id, aws_secret_access_key = get_aws_credentials()

    # 2. Tạo Spark Session
    spark = create_spark_session(aws_access_key_id, aws_secret_access_key)

    # 3. Đọc Parquet từ S3
    s3_file_path = "s3a://zeffmarketingbucket/raw/marketing_campaign_dataset.parquet"
    df = read_parquet_from_s3(spark, s3_file_path)

    # 4. Làm sạch dữ liệu
    df = clean_data(df)

    # 6. Tạo bảng Snowflake & ghi dữ liệu
    sf_options = {
        "sfURL": os.environ.get("SNOWFLAKE_URL"),
        "sfDatabase": os.environ.get("SNOWFLAKE_DB"),
        "sfSchema": os.environ.get("SNOWFLAKE_SCHEMA"),
        "sfWarehouse": os.environ.get("SNOWFLAKE_WAREHOUSE"),
        "sfUser": os.environ.get("SNOWFLAKE_USER"),
        "sfPassword": os.environ.get("SNOWFLAKE_PASSWORD")
    }

    create_table_query = """
    CREATE OR REPLACE TABLE marketing_spark_test (
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

    create_snowflake_table(sf_options, create_table_query)
    write_to_snowflake(df, sf_options, table_name="marketing_spark_test")

    # Đóng SparkSession
    spark.stop()
    print("Spark session stopped. Job completed successfully.")


if __name__ == "__main__":
    # Khi file được gọi trực tiếp (python py_spark_clean.py) thì chạy main()
    main()

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_replace, to_date, trim, upper, lower, when, expr
import pyspark.sql.functions as F
from dotenv import load_dotenv
import os

load_dotenv()
# Lấy thông tin từ file .env
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")


# Bước 1: Khởi tạo SparkSession
spark = SparkSession.builder \
    .master("local") \
    .appName("Read Parquet from S3") \
    .config("spark.jars", "./sparkclean/lib/aws-java-sdk-1.12.778.jar,./sparkclean/lib/hadoop-aws-3.3.4.jar,./sparkclean/lib/jets3t-0.9.4.jar") \
    .config("spark.hadoop.fs.s3a.access.key", "<AWS_ACCESS_KEY>") \
    .config("spark.hadoop.fs.s3a.secret.key", "<AWS_SECRET_KEY>") \
    .config("spark.hadoop.fs.s3a.endpoint", "s3.amazonaws.com") \
    .getOrCreate()


# Bước 3: Đọc file Parquet từ S3
s3_parquet_path = "s3://zeffmarketingbucket/raw/marketing_campaign_dataset.parquet"  # Thay thế bằng đường dẫn của bạn
df = spark.read.parquet(s3_parquet_path)


# Bước 3: Làm sạch cột 'Acquisition_Cost'
df = df.withColumn("Acquisition_Cost", regexp_replace(col("Acquisition_Cost"), r"[\$,]", "").cast("float"))

# Bước 4: Chuyển đổi cột 'Date' sang định dạng ngày tháng
df = df.withColumn("Date", to_date(col("Date"), "yyyy-MM-dd"))

# Bước 5: Làm sạch cột 'Duration'
df = df.withColumn("Duration", regexp_replace(col("Duration"), " days", "").cast("int"))

# Bước 6: Kiểm tra và xử lý giá trị null
missing_values = df.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns])
print("Missing values before cleaning:")
missing_values.show()

# Bước 7: Loại bỏ giá trị âm hoặc không hợp lệ trong các cột số
numeric_columns = ["Conversion_Rate", "ROI", "Clicks", "Impressions", "Engagement_Score"]
for col_name in numeric_columns:
    df = df.filter(col(col_name) >= 0)

# Bước 8: Chuẩn hóa chuỗi văn bản
string_columns = ["Company", "Campaign_Type", "Target_Audience", "Channel_Used", 
                  "Location", "Language", "Customer_Segment"]

for col_name in string_columns:
    df = df.withColumn(col_name, trim(lower(col(col_name))))

# Bước 9: Tính tỷ lệ phần trăm cho Conversion_Rate (nếu cần)
df = df.withColumn("Conversion_Rate", when(col("Conversion_Rate") > 1, col("Conversion_Rate") / 100).otherwise(col("Conversion_Rate")))

# Bước 10: Tách độ tuổi và giới tính từ 'Target_Audience'
df = df.withColumn("Gender", F.regexp_extract(col("Target_Audience"), r"(Men|Women|All)", 1))
df = df.withColumn("Age_Group", F.regexp_extract(col("Target_Audience"), r"(\d+-\d+)", 1))

# Bước 11: Loại bỏ dòng trùng lặp
df = df.dropDuplicates()

# Kiểm tra dữ liệu sau khi làm sạch
print("\nDataset Info After Cleaning:")
df.printSchema()

df.show()



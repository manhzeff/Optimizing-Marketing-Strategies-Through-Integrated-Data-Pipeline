from confluent_kafka.avro import AvroConsumer
import snowflake.connector
import os
from dotenv import load_dotenv

# Tải các biến từ tệp .env
load_dotenv()

# Lấy thông tin kết nối từ biến môi trường
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_TABLE = "campaign_data"

# Kết nối với Snowflake
conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA
)
cursor = conn.cursor()

# Tạo bảng nếu chưa tồn tại
create_table_query = f"""
CREATE TABLE IF NOT EXISTS {SNOWFLAKE_TABLE} (
    Campaign_ID INT,
    Company STRING,
    Campaign_Type STRING,
    Target_Audience STRING,
    Duration STRING,
    Channel_Used STRING,
    Conversion_Rate FLOAT,
    Acquisition_Cost STRING,
    ROI FLOAT,
    Location STRING,
    Language STRING,
    Clicks INT,
    Impressions INT,
    Engagement_Score INT,
    Customer_Segment STRING,
    Date STRING
);
"""
cursor.execute(create_table_query)

def read_messages(batch_size=10000):
    consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "schema.registry.url": "http://localhost:8081",
        "group.id": "practice.bitcoin.avro.consumer.2",
        "auto.offset.reset": "earliest"
    }

    consumer = AvroConsumer(consumer_config)
    consumer.subscribe(["marketing_campaign"])

    batch = []  # Khởi tạo lô dữ liệu
    while True:
        try:
            message = consumer.poll(1)  # Giảm thời gian chờ để lấy tin nhắn nhanh hơn
        except Exception as e:
            print(f"Exception while trying to poll messages - {e}")
            continue
        if message is not None:
            print(f"Successfully polled a record from Kafka topic: {message.topic()}, partition: {message.partition()}, offset: {message.offset()}\n"
                  f"message key: {message.key()} || message value: {message.value()}")
            consumer.commit()

            # Thu thập bản ghi vào lô
            message_value = message.value()
            values = (
                message_value.get('Campaign_ID'),
                message_value.get('Company'),
                message_value.get('Campaign_Type'),
                message_value.get('Target_Audience'),
                message_value.get('Duration'),
                message_value.get('Channel_Used'),
                message_value.get('Conversion_Rate'),
                message_value.get('Acquisition_Cost'),
                message_value.get('ROI'),
                message_value.get('Location'),
                message_value.get('Language'),
                message_value.get('Clicks'),
                message_value.get('Impressions'),
                message_value.get('Engagement_Score'),
                message_value.get('Customer_Segment'),
                message_value.get('Date')
            )
            batch.append(values)

            # Khi đạt batch_size, chèn cả lô vào Snowflake
            if len(batch) >= batch_size:
                insert_query = f"""
                INSERT INTO {SNOWFLAKE_TABLE} (
                    Campaign_ID, Company, Campaign_Type, Target_Audience, Duration, 
                    Channel_Used, Conversion_Rate, Acquisition_Cost, ROI, Location, 
                    Language, Clicks, Impressions, Engagement_Score, Customer_Segment, Date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                cursor.executemany(insert_query, batch)  # Chèn theo lô
                conn.commit()
                batch.clear()  # Xóa lô sau khi chèn xong
        else:
            # Khi không có tin nhắn mới, kiểm tra xem lô hiện tại có dữ liệu để chèn không
            if batch:
                insert_query = f"""
                INSERT INTO {SNOWFLAKE_TABLE} (
                    Campaign_ID, Company, Campaign_Type, Target_Audience, Duration, 
                    Channel_Used, Conversion_Rate, Acquisition_Cost, ROI, Location, 
                    Language, Clicks, Impressions, Engagement_Score, Customer_Segment, Date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                cursor.executemany(insert_query, batch)
                conn.commit()
                batch.clear()
            print("No new messages at this point. Try again later.")

    consumer.close()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    read_messages()

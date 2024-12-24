import boto3
import csv
import os
from confluent_kafka.avro import AvroConsumer
from dotenv import load_dotenv

load_dotenv()

# Config AWS S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY_ID")
)
S3_BUCKET = 'zeffmarketingbucket'
S3_KEY = 'raw/campaign_data.csv'  # Đường dẫn lưu file CSV trong bucket

def write_to_s3_as_csv(data):
    """
    Ghi toàn bộ dữ liệu vào một file CSV và upload lên S3.
    """
    local_file_name = 'campaign_data_combined.csv'  # Tên file tạm
    
    # Ghi tất cả dữ liệu vào file CSV
    try:
        # Lấy danh sách các cột từ khóa của JSON đầu tiên
        fieldnames = data[0].keys() if data else []
        
        # Ghi dữ liệu vào file CSV
        with open(local_file_name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()  # Ghi header
            writer.writerows(data)  # Ghi từng dòng dữ liệu
        
        # Upload file lên S3
        s3_client.upload_file(local_file_name, S3_BUCKET, S3_KEY)
        print(f"Successfully uploaded {local_file_name} to s3://{S3_BUCKET}/{S3_KEY}")
    except Exception as e:
        print(f"Error uploading to S3: {e}")
    finally:
        os.remove(local_file_name)  # Xóa file tạm sau khi upload

def read_messages_to_s3():
    """
    Đọc tất cả tin nhắn Kafka và lưu vào một file CSV duy nhất trên S3.
    """
    consumer_config = {
        "bootstrap.servers": "localhost:9092",
        "schema.registry.url": "http://localhost:8081",
        "group.id": "practice.bitcoin.avro.consumer.2",
        "auto.offset.reset": "earliest"
    }
    consumer = AvroConsumer(consumer_config)
    consumer.subscribe(["marketing_campaign"])

    all_data = []  # Danh sách để gom toàn bộ dữ liệu Kafka

    print("Starting to read messages from Kafka...")
    while True:
        try:
            message = consumer.poll(1)
        except Exception as e:
            print(f"Exception while polling messages - {e}")
            continue

        if message is not None:
            message_value = message.value()
            all_data.append(message_value)  # Thêm dữ liệu vào danh sách
        else:
            print("No new messages. Stopping consumer...")
            break

    consumer.close()

    # Upload toàn bộ dữ liệu lên S3 dưới dạng CSV
    if all_data:
        print(f"Total messages fetched: {len(all_data)}")
        write_to_s3_as_csv(all_data)
    else:
        print("No data fetched. Nothing to upload.")

if __name__ == "__main__":
    read_messages_to_s3()

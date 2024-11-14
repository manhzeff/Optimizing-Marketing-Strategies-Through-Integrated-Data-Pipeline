from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer
from confluent_kafka.admin import AdminClient, NewTopic
import csv
from time import sleep

def load_avro_schema_from_file():
    key_schema = avro.load("marketing_key.avsc")
    value_schema = avro.load("marketing_value.avsc")
    return key_schema, value_schema

def create_topic_if_not_exists(topic_name, num_partitions, replication_factor=1):
    admin_client = AdminClient({"bootstrap.servers": "localhost:9092"})
    
    # Kiểm tra xem topic đã tồn tại hay chưa
    topic_metadata = admin_client.list_topics(timeout=5)
    if topic_name not in topic_metadata.topics:
        # Tạo topic nếu chưa tồn tại
        topic = NewTopic(topic=topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
        admin_client.create_topics([topic])
        print(f"Topic '{topic_name}' created with {num_partitions} partitions.")
    else:
        print(f"Topic '{topic_name}' already exists.")

def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def send_record():
    key_schema, value_schema = load_avro_schema_from_file()
    topic_name = 'marketing_campaign'
    num_partitions = 10  # Số phân vùng mong muốn cho topic

    # Tạo topic với số phân vùng nếu chưa tồn tại
    create_topic_if_not_exists(topic_name, num_partitions)

    producer_config = {
        "bootstrap.servers": "localhost:9092",
        "schema.registry.url": "http://localhost:8081",
        "acks": "1",
        "linger.ms": 100,
        "batch.size": 131072,
        "queue.buffering.max.messages": 200000,
        "queue.buffering.max.kbytes": 2097152,
        "retries": 15,
        "retry.backoff.ms": 100,
    }

    producer = AvroProducer(producer_config, default_key_schema=key_schema, default_value_schema=value_schema)

    with open('data/marketing_campaign_dataset.csv') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        for row in csvreader:
            key = {"Campaign_ID": int(row[0])}
            value = {
                "Campaign_ID": int(row[0]),
                "Company": str(row[1]),
                "Campaign_Type": str(row[2]),
                "Target_Audience": str(row[3]),
                "Duration": str(row[4]),
                "Channel_Used": str(row[5]),
                "Conversion_Rate": float(row[6]),
                "Acquisition_Cost": str(row[7].replace('$', '').replace(',', '')),
                "ROI": float(row[8]),
                "Location": str(row[9]),
                "Language": str(row[10]),
                "Clicks": int(row[11]),
                "Impressions": int(row[12]),
                "Engagement_Score": int(row[13]),
                "Customer_Segment": str(row[14]),
                "Date": str(row[15])
            }

            try:
                producer.produce(topic=topic_name, key=key, value=value, callback=delivery_report)
            except Exception as e:
                print(f"Exception while producing record value - {value}: {e}")

    # Flush tất cả các bản ghi đã sản xuất khi hoàn thành
    producer.flush()

if __name__ == "__main__":
    send_record()
